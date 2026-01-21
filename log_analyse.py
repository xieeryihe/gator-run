import os


def analyse_log(log_file_path):
    """
    格式为：
    [HIER] All classes: 2406 [App: 1292, Lib : 1051, Phantom: 63]
    [HIER] Activities: 11, lib activities: 2
    [HIER] App views: 8, Lib views: 53
    [HIER] App Dialogs: 0, Lib Dialogs: 3
    提取Activities, lib activities, App Dialogs, Lib Dialogs 四个信息
    """
    results = {}
    with open(log_file_path, 'r', encoding='utf-8') as f:
        total_num = 0
        for line in f:
            line = line.strip()
            if line.startswith("[HIER] Activities:"):
                parts = line.split(',')
                activities_part = parts[0].split(':')[1].strip()
                lib_activities_part = parts[1].split(':')[1].strip()
                results['Activities'] = int(activities_part)
                results['Lib activities'] = int(lib_activities_part)
                total_num += int(activities_part) + int(lib_activities_part)
            elif line.startswith("[HIER] App Dialogs:"):
                parts = line.split(',')
                app_dialogs_part = parts[0].split(':')[1].strip()
                lib_dialogs_part = parts[1].split(':')[1].strip()
                results['App Dialogs'] = int(app_dialogs_part)
                results['Lib Dialogs'] = int(lib_dialogs_part)
                total_num += int(app_dialogs_part) + int(lib_dialogs_part)
        results['Total'] = total_num

    return results

def analyse_dir(dir_path):
    """分析目录下所有log文件"""
    all_results = {}
    for filename in os.listdir(dir_path):
        work_dir = os.path.join(dir_path, filename)
        log_file_path = os.path.join(work_dir, 'log.txt')
        if os.path.exists(log_file_path):
            results = analyse_log(log_file_path)
            all_results[filename] = results
        else:
            print(f"日志文件不存在: {log_file_path}")
    return all_results

def write_excel(data, excel_file_path):
    """将数据写入Excel文件"""
    import pandas as pd
    df = pd.DataFrame.from_dict(data, orient='index')
    df.to_excel(excel_file_path)

if __name__ == "__main__":
    task_dir = "bak\\task_2025-12-29_15-51-03"
    results = analyse_dir(task_dir)
    excel_file_path = 'analysis_results.xlsx'
    write_excel(results, excel_file_path)
    print(f"分析结果已写入: {excel_file_path}")