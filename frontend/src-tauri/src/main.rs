// kanbun-kakikudashi 桌面壳（D6: Night 14 sidecar 随壳启动）
//
// 启动顺序：
//   1. 先探测本机 8000-8009 是否已有后端（用户可能自己开了 start_backend.bat，
//      或上次 sidecar 没退干净）——有就复用，不重复起。
//   2. 没有就启动随包的 kanbun-sidecar.exe，从 stdout 读 `KANBUN_PORT=<n>`。
//   3. 窗口直接指向 http://127.0.0.1:<port>/：后端同时托管前端（同源，零 CORS）。
//      后端用 KANBUN_LAZY_ENGINE=1 启动，端口先让出来、引擎后台加载，
//      所以窗口能立刻打开，前端自己显示「引擎加载中」并轮询 /health。
//   4. 窗口关闭 / 进程退出时结束子进程。
//
// 找不到 sidecar 也不崩：开发机上常只有 python 没有打包产物，这时回退到
// 8000 并打印提示，方便调试。
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{BufRead, BufReader};
use std::net::{SocketAddr, TcpStream};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use tauri::{Manager, RunEvent, WebviewUrl, WebviewWindowBuilder};

const DEFAULT_PORT: u16 = 8000;
const PORT_PROBE_END: u16 = 8010;

/// 端口上有没有东西在监听（只做 TCP 连接，不发 HTTP）。
fn listening(port: u16) -> bool {
    let addr: SocketAddr = match format!("127.0.0.1:{}", port).parse() {
        Ok(a) => a,
        Err(_) => return false,
    };
    TcpStream::connect_timeout(&addr, Duration::from_millis(250)).is_ok()
}

fn find_running_backend() -> Option<u16> {
    (DEFAULT_PORT..PORT_PROBE_END).find(|p| listening(*p))
}

/// sidecar 可执行文件的候选位置，按「最可能是真的」排序。
///
/// 布局说明（onedir PyInstaller 产物，必须整个目录一起走）：
///   - 打包后：<install_dir>/kanbun-sidecar/kanbun-sidecar.exe
///     （tauri.conf.json 的 resources 把 sidecar/ 原样拷进安装目录）
///   - 开发：target/release -> ../../../dist/kanbun-sidecar/kanbun-sidecar.exe
fn sidecar_candidates(resource_dir: Option<PathBuf>) -> Vec<PathBuf> {
    let mut out = Vec::new();
    if let Some(res) = resource_dir {
        // resources 里是 sidecar/kanbun-sidecar.exe
        out.push(res.join("sidecar").join("kanbun-sidecar.exe"));
        out.push(res.join("kanbun-sidecar").join("kanbun-sidecar.exe"));
        out.push(res.join("kanbun-sidecar.exe"));
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            out.push(dir.join("kanbun-sidecar").join("kanbun-sidecar.exe"));
            out.push(dir.join("sidecar").join("kanbun-sidecar.exe"));
            out.push(dir.join("kanbun-sidecar.exe"));
            // 开发：target/release -> 项目根/dist/kanbun-sidecar/
            out.push(
                dir.join("..")
                    .join("..")
                    .join("..")
                    .join("..")
                    .join("dist")
                    .join("kanbun-sidecar")
                    .join("kanbun-sidecar.exe"),
            );
        }
    }
    out
}

fn spawn_sidecar(resource_dir: Option<PathBuf>) -> Option<Child> {
    for path in sidecar_candidates(resource_dir) {
        if !path.is_file() {
            continue;
        }
        let mut cmd = Command::new(&path);
        cmd.stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .env("KANBUN_LAZY_ENGINE", "1")
            .env("KANBUN_SIDECAR", "1");
        match cmd.spawn() {
            Ok(child) => {
                eprintln!("[kanbun] sidecar 已启动: {}", path.display());
                return Some(child);
            }
            Err(e) => eprintln!("[kanbun] 启动失败 {}: {}", path.display(), e),
        }
    }
    eprintln!("[kanbun] 未找到 kanbun-sidecar.exe（开发环境请自行启动后端）");
    None
}

/// 从 sidecar stdout 读第一行 `KANBUN_PORT=<n>`。超时返回 None。
fn read_sidecar_port(child: &mut Child, timeout: Duration) -> Option<u16> {
    let stdout = child.stdout.take()?;
    let (tx, rx) = std::sync::mpsc::channel::<String>();
    std::thread::spawn(move || {
        for line in BufReader::new(stdout).lines().map_while(Result::ok) {
            if tx.send(line).is_err() {
                break;
            }
        }
    });

    let deadline = Instant::now() + timeout;
    loop {
        let left = deadline.saturating_duration_since(Instant::now());
        if left.is_zero() {
            return None;
        }
        match rx.recv_timeout(left) {
            Ok(line) => {
                if let Some(rest) = line.strip_prefix("KANBUN_PORT=") {
                    if let Ok(p) = rest.trim().parse::<u16>() {
                        return Some(p);
                    }
                }
            }
            Err(_) => return None,
        }
    }
}

struct AppState {
    child: Mutex<Option<Child>>,
}

fn main() {
    tauri::Builder::default()
        .manage(AppState {
            child: Mutex::new(None),
        })
        .setup(|app| {
            // 到这里才有 resource_dir()，所以 sidecar 的启动放在 setup 里。
            let resource_dir = app.path().resource_dir().ok();

            let (port, spawned) = match find_running_backend() {
                Some(p) => {
                    eprintln!("[kanbun] 复用已在运行的后端: 127.0.0.1:{}", p);
                    (p, None)
                }
                None => match spawn_sidecar(resource_dir) {
                    Some(mut child) => {
                        let p = read_sidecar_port(&mut child, Duration::from_secs(60))
                            .unwrap_or(DEFAULT_PORT);
                        eprintln!("[kanbun] sidecar 端口 {}", p);
                        (p, Some(child))
                    }
                    None => (DEFAULT_PORT, None),
                },
            };

            if let Some(state) = app.try_state::<AppState>() {
                if let Ok(mut guard) = state.child.lock() {
                    *guard = spawned;
                }
            }

            let url = format!("http://127.0.0.1:{}/", port);
            WebviewWindowBuilder::new(app, "main", WebviewUrl::External(url.parse()?))
                .title("漢文 → 書き下し文")
                .inner_size(1280.0, 860.0)
                .build()?;
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let RunEvent::Exit = event {
                if let Some(state) = app.try_state::<AppState>() {
                    if let Ok(mut guard) = state.child.lock() {
                        if let Some(child) = guard.as_mut() {
                            eprintln!("[kanbun] 结束 sidecar (pid {})", child.id());
                            let _ = child.kill();
                            let _ = child.wait();
                        }
                    }
                }
            }
        });
}
