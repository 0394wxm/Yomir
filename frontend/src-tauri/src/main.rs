// kanbun-kakikudashi 桌面壳（Night 13 脚手架）。
// Night 14 计划：把 Python 后端作为 sidecar 随壳启动；
// 本脚手架阶段先加载开发服务器 URL（devUrl），API 调用需后端在 8000 端口运行。
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
