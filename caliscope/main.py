from pathlib import Path
from workspace_guide import WorkspaceGuide

def main():
    # 設置您的工作目錄路徑
    workspace_dir = Path("你的工作目錄路徑")
    
    # 設置攝像頭數量
    camera_count = 4  # 根據實際需求修改
    
    # 創建 WorkspaceGuide 實例
    guide = WorkspaceGuide(workspace_dir, camera_count)
    
    # 獲取並打印工作區狀態
    summary = guide.get_html_summary()
    print(summary)
    
    # 檢查校準狀態
    print("\n校準狀態：")
    print(f"內部校準狀態：{guide.intrinsic_calibration_status()}")
    print(f"外部校準狀態：{guide.extrinsic_calibration_status()}")
    
    # 檢查有效的錄製目錄
    print("\n有效的錄製目錄：")
    print(guide.valid_recording_dirs())

if __name__ == "__main__":
    main() 