use serde::{Deserialize, Serialize};
use std::process::Command;
use tauri::Manager;

#[derive(Debug, Serialize, Deserialize, Clone)]
struct EditorMessage {
    r#type: String, // 'type' is a reserved keyword in Rust
    #[serde(flatten)]
    extra: serde_json::Value,
}

#[tauri::command]
async fn handle_frontend_message(
    _app: tauri::AppHandle,
    message: EditorMessage,
) -> Result<(), String> {
    println!("Received message from frontend: {:?}", message);
    Ok(())
}

fn get_python_interpreter() -> String {
    // First, try to find relative to executable (for production builds)
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            // Check for .venv (Unix)
            let dot_venv_bin = exe_dir.join(".venv/bin/python3");
            if dot_venv_bin.exists() {
                return dot_venv_bin.to_string_lossy().to_string();
            }

            // Check for venv (Unix)
            let venv_bin = exe_dir.join("venv/bin/python3");
            if venv_bin.exists() {
                return venv_bin.to_string_lossy().to_string();
            }

            // Check for .venv (Windows)
            let dot_venv_win = exe_dir.join(".venv/Scripts/python.exe");
            if dot_venv_win.exists() {
                return dot_venv_win.to_string_lossy().to_string();
            }

            // Check for venv (Windows)
            let venv_win = exe_dir.join("venv/Scripts/python.exe");
            if venv_win.exists() {
                return venv_win.to_string_lossy().to_string();
            }
        }
    }

    // Fallback: try current directory (for dev builds)
    let current_dir = std::env::current_dir().unwrap_or_default();

    // Check for .venv (Unix)
    let dot_venv_bin = current_dir.join(".venv/bin/python3");
    if dot_venv_bin.exists() {
        return dot_venv_bin.to_string_lossy().to_string();
    }

    // Check for venv (Unix)
    let venv_bin = current_dir.join("venv/bin/python3");
    if venv_bin.exists() {
        return venv_bin.to_string_lossy().to_string();
    }

    // Check for .venv (Windows)
    let dot_venv_win = current_dir.join(".venv/Scripts/python.exe");
    if dot_venv_win.exists() {
        return dot_venv_win.to_string_lossy().to_string();
    }

    // Check for venv (Windows)
    let venv_win = current_dir.join("venv/Scripts/python.exe");
    if venv_win.exists() {
        return venv_win.to_string_lossy().to_string();
    }

    // Fallback to system python3
    "python3".to_string()
}

fn run_python_script(
    command: &str,
    params: serde_json::Value,
) -> Result<serde_json::Value, String> {
    // Locate python script relative to the executable
    let exe_path = std::env::current_exe().map_err(|e| e.to_string())?;
    let exe_dir = exe_path
        .parent()
        .ok_or_else(|| "Failed to get executable directory".to_string())?;
    let py_script = exe_dir.join("python/py/py_bridge.py");

    if !py_script.exists() {
        return Err(format!("Python script not found at {:?}", py_script));
    }

    let params_str = serde_json::to_string(&params).map_err(|e| e.to_string())?;
    let python_exe = get_python_interpreter();

    println!("Using Python interpreter: {}", python_exe);

    let output = Command::new(python_exe)
        .arg(&py_script)
        .arg(command)
        .arg(params_str)
        .output()
        .map_err(|e| e.to_string())?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python script failed: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let res: serde_json::Value = serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse Python output: {}. Output: {}", e, stdout))?;
    Ok(res)
}

#[tauri::command]
async fn query_db(
    db_path: String,
    query: String,
    key: Option<String>,
) -> Result<serde_json::Value, String> {
    let params = serde_json::json!({
        "db_path": db_path,
        "query": query,
        "key": key
    });
    run_python_script("query_db", params)
}

#[tauri::command]
async fn extract_story_data(params: serde_json::Value) -> Result<serde_json::Value, String> {
    run_python_script("extract_story_data", params)
}

#[tauri::command]
async fn extract_voice(params: serde_json::Value) -> Result<serde_json::Value, String> {
    run_python_script("extract_voice", params)
}

#[tauri::command]
async fn extract_lyrics_data(params: serde_json::Value) -> Result<serde_json::Value, String> {
    run_python_script("extract_lyrics_data", params)
}

#[tauri::command]
async fn extract_race_story_data(params: serde_json::Value) -> Result<serde_json::Value, String> {
    run_python_script("extract_race_story_data", params)
}

#[tauri::command]
async fn read_text_file(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path).map_err(|e| e.to_string())
}

#[tauri::command]
async fn write_text_file(path: String, content: String) -> Result<(), String> {
    std::fs::write(&path, content).map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            handle_frontend_message,
            query_db,
            extract_story_data,
            extract_voice,
            extract_lyrics_data,
            extract_race_story_data,
            read_text_file,
            write_text_file
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
