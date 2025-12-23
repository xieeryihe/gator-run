import os, sys
import json, subprocess, glob
import tempfile, shutil
import threading
import re
import time
from datetime import datetime

GLOBAL_DECODE_LOCK = threading.Lock()

# ========== Configuration ==========
# You can modify these default values or use a config file
DEFAULT_CONFIG = {
    "gator_root": r"C:\Code\experiment\Gator",
    "adk_root": r"D:\AndroidSDK",
    "java_memory": "12G",
    "apktool_jar": "apktool_2.9.1.jar",
    "apk_directory": r"C:\Code\experiment\Gator\AndroidBench\apk",
    "analysis_timeout": 600  # 10 minutes default timeout
}

def loadConfig():
    """Load configuration from config file or use defaults"""
    configPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "gator_config.json")
    if os.path.exists(configPath):
        try:
            with open(configPath, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"[OK] Loaded config from: {configPath}")
                return config
        except Exception as e:
            print(f"[WARN] Failed to load config file ({e}), using defaults")
    else:
        print(f"[INFO] Config file not found at {configPath}, using defaults")
    return DEFAULT_CONFIG

CONFIG = loadConfig()
# ===================================

class GlobalConfigs:
    def __init__(self):
      self.APK_NAME=""
      self.GATOR_ROOT=""
      self.ADK_ROOT=""
      self.APKTOOL_PATH=""
      self.GATOR_OPTIONS=[]
      self.KEEP_DECODE=False

def fatalError(str):
    print(str)
    sys.exit(1)
    pass

def extractLibsFromPath(pathName):
    if not pathExists(pathName):
        return []
    return glob.glob(os.path.join(pathName, "*.jar"))

def pathExists(pathName):
    if os.access(pathName, os.F_OK):
        return True
    return False
    pass

def invokeGatorOnAPK(\
                apkPath,
                resPath,
                manifestPath,
                apiLevel,
                sdkLocation,
                benchmarkName,
                options,
                configs,
                output = None,
                timeout = 0
                ):
    ''''''
    SootAndroidLocation = os.path.join(configs.GATOR_ROOT, "SootAndroid")
    bGoogleAPI = False
    if len(apiLevel) > 6:
        if apiLevel[:6] == "google":
            bGoogleAPI = True
    sLevelNum = apiLevel[apiLevel.find('-') + 1:]
    try:
        iLevelNum = int(sLevelNum)
    except:
        fatalError("FATALERROR: API Level not valid")
    if (bGoogleAPI):
        GoogleAPIDir = os.path.join(sdkLocation, "add-ons", "addon-google_apis-google-" + sLevelNum)
        if not pathExists(GoogleAPIDir) :
            print("Google API Level:" + sLevelNum + "Not installed!")
            sys.exit(-1);
        GoogleAPI = os.pathsep.join([
            os.path.join(GoogleAPIDir, "libs", "maps.jar"),
            os.path.join(GoogleAPIDir, "libs", "usb.jar"),
            os.path.join(GoogleAPIDir, "libs", "effects.jar")])
    classPathEntries = [os.path.join(SootAndroidLocation, "bin")]
    classPathEntries.extend(extractLibsFromPath(os.path.join(SootAndroidLocation, "lib")))
    ClassPathJar = os.pathsep.join(classPathEntries)
    platformJarEntries = [os.path.join(sdkLocation, "platforms", "android-" + sLevelNum, "android.jar")]
    supportLibs = [
        "android-support-annotations.jar",
        "android-support-v4.jar",
        "android-support-v7-appcompat.jar",
        "android-support-v7-cardview.jar",
        "android-support-v7-gridlayout.jar",
        "android-support-v7-mediarouter.jar",
        "android-support-v7-palette.jar",
        "android-support-v7-preference.jar",
        "android-support-v7-recyclerview.jar"
    ]
    platformJarEntries.extend([os.path.join(SootAndroidLocation, "deps", lib) for lib in supportLibs])
    if iLevelNum >= 23:
        #include the apache library
        apacheLib = os.path.join(sdkLocation, "platforms", "android-" + sLevelNum, "optional", "org.apache.http.legacy.jar")
        if pathExists(apacheLib):
            platformJarEntries.append(apacheLib)
    PlatformJar = os.pathsep.join(platformJarEntries)
    #Finished computing platform libraries
    callList = [\
                'java', \
                f'-Xmx{CONFIG["java_memory"]}', \
                '-classpath', ClassPathJar, \
                'presto.android.Main', \
                '-project', apkPath,\
                '-android', PlatformJar,\
                '-sdkDir', sdkLocation,\
                '-classFiles', apkPath, \
                '-resourcePath', resPath, \
                '-manifestFile', manifestPath,\
                '-apiLevel', "android-" + sLevelNum,\
                '-benchmarkName', benchmarkName,\
                '-guiAnalysis',
                '-listenerSpecFile', os.path.join(SootAndroidLocation, "listeners.xml"),
                '-wtgSpecFile', os.path.join(SootAndroidLocation, 'wtg.xml')]
    callList.extend(options);
    #print(callList)
    
    # Set up environment with GatorRoot
    env = os.environ.copy()
    env['GatorRoot'] = configs.GATOR_ROOT
    
    if timeout == 0:
        return subprocess.call(callList, stdout = output, stderr = output, env = env)
    else:
        # Use Popen for better timeout control and forced termination
        try:
            process = subprocess.Popen(
                callList,
                stdout=output,
                stderr=output,
                env=env
            )
            retval = process.wait(timeout=timeout)
            return retval
        except subprocess.TimeoutExpired:
            # Try graceful termination first to allow Java to save data
            if output:
                output.write(f"\n[WARNING] Analysis timeout after {timeout}s, attempting graceful shutdown...\n")
                output.flush()
            
            process.terminate()  # Send SIGTERM (graceful)
            try:
                retval = process.wait(timeout=10)  # Wait 10 seconds for graceful exit
                if output:
                    output.write(f"[INFO] Process terminated gracefully\n")
                    output.flush()
                return retval
            except subprocess.TimeoutExpired:
                # Force kill if graceful termination fails
                if output:
                    output.write(f"[ERROR] Graceful termination failed, force killing process\n")
                    output.flush()
                process.kill()
                process.wait()
            
            if output:
                try:
                    os.fsync(output.fileno())  # Force write to disk
                except:
                    pass
            return -50
    pass

def decodeAPK(apkPath, decodeLocation, output = None):
    global GLOBAL_DECODE_LOCK
    GLOBAL_DECODE_LOCK.acquire()
    callList = ['java',\
                '-jar',\
                CONFIG["apktool_jar"],\
                'd', apkPath,\
                '-o', decodeLocation, \
                '-f']
    ret = subprocess.call(callList, stdout = output, stderr = None)
    GLOBAL_DECODE_LOCK.release()
    if ret != 0:
        fatalError("APK Decode Failed!")
    pass

def parseMainParam():
    params = sys.argv
    configs=GlobalConfigs()
    determinGatorRootAndSDKPath(configs)
    i = 0
    while i < len(params) - 1:
        i += 1
        var = params[i]
        if (var[-4:] == ".apk") and (configs.APK_NAME == ""):
            configs.APK_NAME = var
            continue
        if var == "--keep-decoded-apk-dir":
            configs.KEEP_DECODE = True
            continue
        configs.GATOR_OPTIONS.append(var)
        pass
    return configs

def determinAPILevel(dirName, configs):
    targetLevel = 0;
    apktoolFile = os.path.join(dirName, "apktool.yml")
    if pathExists(apktoolFile):
        infoFile = open(apktoolFile, 'r')
        lines = infoFile.readlines()
        infoFile.close()
        for i in range(len(lines)):
            if "targetSdkVersion" in lines[i]:
                targetLevel = extractAPILevelFromLine(lines[i])
            elif "minSdkVersion" in lines[i]:
                minLevel = extractAPILevelFromLine(lines[i])
                if minLevel > targetLevel:
                    targetLevel = minLevel
        if (targetLevel != 0):
            adkPlatform = os.path.join(configs.ADK_ROOT, "platforms", "android-" + str(targetLevel))
            if pathExists(adkPlatform):
                return targetLevel
            else:
                return 23
        else:
            return 23
    else:
        return 23

def extractAPILevelFromLine(curLine):
    match = re.search(r"(\d+)", curLine)
    if not match:
        fatalError("Unable to parse API level from apktool.yml")
    return int(match.group(1))

def determinGatorRootAndSDKPath(configs):
    # Determine Gator Root
    gatorRoot = os.environ.get("GatorRoot") or os.environ.get("GATOR_ROOT")
    if gatorRoot != None:
        configs.GATOR_ROOT = os.path.normpath(gatorRoot)
        print(f"[OK] Using GatorRoot from environment: {configs.GATOR_ROOT}")
    else:
        # Try to detect from current directory
        curPath = os.path.abspath(os.getcwd())
        if os.path.basename(curPath) == "AndroidBench":
            configs.GATOR_ROOT = getParentDir(curPath)
            print(f"[OK] Detected GatorRoot from current directory: {configs.GATOR_ROOT}")
        elif "gator_root" in CONFIG and pathExists(CONFIG["gator_root"]):
            configs.GATOR_ROOT = os.path.normpath(CONFIG["gator_root"])
            print(f"[OK] Using GatorRoot from config: {configs.GATOR_ROOT}")
        else:
            print(f"[ERROR] Cannot determine GatorRoot!")
            print(f"  - Environment variable not set")
            print(f"  - Current directory: {curPath}")
            print(f"  - Config gator_root: {CONFIG.get('gator_root', 'NOT SET')}")
            if "gator_root" in CONFIG:
                print(f"  - Config path exists: {pathExists(CONFIG['gator_root'])}")
            fatalError("GatorRoot path not found. Please set environment variable or update config file.")
    
    # Determine ADK Root
    adkRoot = os.environ.get("ADK")
    if adkRoot != None:
        configs.ADK_ROOT = os.path.normpath(adkRoot)
        print(f"[OK] Using ADK from environment: {configs.ADK_ROOT}")
    elif "adk_root" in CONFIG and pathExists(CONFIG["adk_root"]):
        configs.ADK_ROOT = os.path.normpath(CONFIG["adk_root"])
        print(f"[OK] Using ADK from config: {configs.ADK_ROOT}")
    else:
        homeDir = os.environ.get("HOME")
        if homeDir != None:
            if sys.platform == "linux2":
                candidate = os.path.join(homeDir, "Android", "Sdk")
                if pathExists(candidate):
                    configs.ADK_ROOT = candidate
                    print(f"[OK] Found ADK at: {configs.ADK_ROOT}")
                    return
            elif sys.platform == "darwin":
                candidate = os.path.join(homeDir, "Library", "Android", "sdk")
                if pathExists(candidate):
                    configs.ADK_ROOT = candidate
                    print(f"[OK] Found ADK at: {configs.ADK_ROOT}")
                    return
        
        print(f"[ERROR] Cannot determine ADK path!")
        print(f"  - Environment variable ADK not set")
        print(f"  - Config adk_root: {CONFIG.get('adk_root', 'NOT SET')}")
        if "adk_root" in CONFIG:
            print(f"  - Config path exists: {pathExists(CONFIG['adk_root'])}")
        fatalError("ADK path not found. Please set environment variable or update config file.")

def getParentDir(pathName):
    normalized = os.path.normpath(pathName.strip())
    parent = os.path.dirname(normalized)
    if parent and parent != normalized:
        return parent
    fatalError(f"Cannot determine parent directory of: {pathName}")

def runGatorOnAPKDirect(apkFileName, GatorOptions, keepdecodedDir, output = None, configs = None, timeout = 0, taskName = None):
    # Record start time
    start_time = time.time()
    
    if configs == None:
      configs = GlobalConfigs()
    if configs.GATOR_ROOT == "" or configs.ADK_ROOT == "":
        determinGatorRootAndSDKPath(configs)
    
    # Extract app name from apk file
    apkBaseName = os.path.basename(apkFileName)
    appName = apkBaseName.replace(".apk", "").replace(".zip", "")
    
    # Create output directory with timestamp and app name: output/task_2025-12-18_21-22-01/Calendar/
    if taskName is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        taskName = f"task_{timestamp}"
    outputBaseDir = os.path.normpath(os.path.join(configs.GATOR_ROOT, "output", taskName, appName))
    
    # Use temp directory for decoded APK (will always be deleted)
    tempDir = tempfile.mkdtemp(prefix="gator_decode_")
    decodeDir = os.path.normpath(os.path.join(tempDir, "source"))
    os.makedirs(decodeDir, exist_ok=True)
    os.makedirs(outputBaseDir, exist_ok=True)
    
    if output == None:
      print("Extract APK to temporary directory: " + decodeDir)
      print("Results will be saved to: " + outputBaseDir)
    else:
      output.write("Extract APK to temporary directory: " + decodeDir + "\n")
      output.write("Results will be saved to: " + outputBaseDir + "\n")
    
    configs.KEEP_DECODE = keepdecodedDir
    configs.APK_NAME = apkFileName
    configs.GATOR_OPTIONS = GatorOptions
    
    # Ensure WTGVisualizationClient is used if no client is specified
    has_client = any('-client' in opt for opt in configs.GATOR_OPTIONS)
    if not has_client:
        configs.GATOR_OPTIONS.extend(['-client', 'WTGVisualizationClient'])
        if output == None:
            print("[INFO] Using default client: WTGVisualizationClient")
        else:
            output.write("[INFO] Using default client: WTGVisualizationClient\n")

    decodeAPK(configs.APK_NAME, decodeDir, output = output)
    numAPILevel = determinAPILevel(decodeDir, configs)

    manifestPath = decodeDir + "/AndroidManifest.xml"
    resPath = decodeDir + "/res"
    
    # Record Gator execution start
    gator_start = time.time()
    retval = invokeGatorOnAPK(\
                apkPath = configs.APK_NAME,\
                resPath = resPath, \
                manifestPath = manifestPath,\
                apiLevel = "android-{0}".format(numAPILevel), \
                sdkLocation = configs.ADK_ROOT, \
                benchmarkName = f"{taskName}/{appName}",\
                options = configs.GATOR_OPTIONS,
                configs = configs,
                output = output,
                timeout = timeout)
    gator_end = time.time()
    
    # Ensure all output is flushed to disk before continuing
    if output:
        output.flush()
        os.fsync(output.fileno())  # Force write to disk
    
    # Small delay to ensure file system operations complete
    time.sleep(0.5)
    
    # Calculate execution time here before updating JSON
    end_time = time.time()
    total_time = end_time - start_time
    gator_time = gator_end - gator_start

    # Add timing information to the generated wtg.json file and reorganize
    wtg_json_path = os.path.join(outputBaseDir, "wtg.json")
    if os.path.exists(wtg_json_path):
        try:
            with open(wtg_json_path, 'r', encoding='utf-8') as f:
                wtg_data = json.load(f)
            
            # Create new ordered dict with timing info at the beginning
            ordered_data = {
                'analysis_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'analysis_duration_seconds': round(total_time, 3)
            }
            # Add rest of the data
            for key, value in wtg_data.items():
                ordered_data[key] = value
            
            # Write reorganized JSON back
            with open(wtg_json_path, 'w', encoding='utf-8') as f:
                json.dump(ordered_data, f, indent=2, ensure_ascii=False)
            
            if output:
                output.write(f"[INFO] Added timing information to wtg.json: {total_time:.3f}s\n")
        except Exception as e:
            if output:
                output.write(f"[WARNING] Failed to add timing information to wtg.json: {e}\n")
            else:
                print(f"[WARNING] Failed to add timing information to wtg.json: {e}")

    # Always clean up temporary decoded APK directory
    try:
        shutil.rmtree(tempDir)
        if output == None:
          print("Temporary APK resources removed!")
        else:
          output.write("Temporary APK resources removed!\n")
    except Exception as e:
        if output == None:
          print(f"Warning: Failed to remove temporary directory: {e}")
        else:
          output.write(f"Warning: Failed to remove temporary directory: {e}\n")
    
    # Print timing information (time already calculated above)
    if output == None:
        print(f"\n[SUCCESS] Analysis complete!")
        print(f"[TIMING] Total execution time: {total_time:.2f}s")
        print(f"[TIMING] Gator analysis time: {gator_time:.2f}s")
        print(f"[OUTPUT] Results directory: {outputBaseDir}")
    else:
        output.write(f"\n[SUCCESS] Analysis complete!\n")
        output.write(f"[TIMING] Total execution time: {total_time:.2f}s\n")
        output.write(f"[TIMING] Gator analysis time: {gator_time:.2f}s\n")
        output.write(f"[OUTPUT] Results directory: {outputBaseDir}\n")
    
    return retval

def runGatorOnAllAPKsInDirectory(apkDirectory, GatorOptions, keepdecodedDir, configs=None, timeout=None):
    """Run Gator analysis on all APK files in the specified directory"""
    if configs is None:
        configs = GlobalConfigs()
    
    if configs.GATOR_ROOT == "" or configs.ADK_ROOT == "":
        determinGatorRootAndSDKPath(configs)
    
    # Use timeout from config if not specified
    if timeout is None:
        timeout = CONFIG.get("analysis_timeout", 600)
    
    print(f"[INFO] Analysis timeout: {timeout}s ({timeout//60} minutes)")
    
    # Find all APK files in the directory
    if not pathExists(apkDirectory):
        print(f"[ERROR] APK directory not found: {apkDirectory}")
        return -1
    
    apkFiles = glob.glob(os.path.join(apkDirectory, "*.apk"))
    if not apkFiles:
        print(f"[WARNING] No APK files found in: {apkDirectory}")
        return 0
    
    # Create a single timestamp for all APKs in this batch
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    taskName = f"task_{timestamp}"
    
    print(f"\n[INFO] Found {len(apkFiles)} APK file(s) in {apkDirectory}")
    print(f"[INFO] Batch task: {taskName}")
    print(f"[INFO] Starting batch analysis...\n")
    
    results = []
    for idx, apkPath in enumerate(apkFiles, 1):
        apkName = os.path.basename(apkPath)
        print(f"\n{'='*60}")
        print(f"[{idx}/{len(apkFiles)}] Processing: {apkName}")
        print(f"{'='*60}\n")
        
        # Create log file for each APK
        appName = apkName.replace(".apk", "").replace(".zip", "")
        logDir = os.path.join(configs.GATOR_ROOT, "output", taskName, appName)
        os.makedirs(logDir, exist_ok=True)
        logPath = os.path.join(logDir, "log.txt")
        
        with open(logPath, 'w', encoding='utf-8') as logFile:
            retval = runGatorOnAPKDirect(
                apkPath, 
                GatorOptions, 
                keepdecodedDir, 
                output=logFile, 
                configs=configs,
                timeout=timeout,
                taskName=taskName
            )
            results.append((apkName, retval))
        
        if retval == 0:
            print(f"[✓] {apkName} - SUCCESS")
        elif retval == -50:
            print(f"[✗] {apkName} - TIMEOUT")
        else:
            print(f"[✗] {apkName} - FAILED (exit code: {retval})")
    
    # Print summary
    print(f"\n{'='*60}")
    print("BATCH ANALYSIS SUMMARY")
    print(f"{'='*60}")
    success_count = sum(1 for _, ret in results if ret == 0)
    print(f"Total: {len(results)} | Success: {success_count} | Failed: {len(results) - success_count}")
    for apkName, retval in results:
        status = "SUCCESS" if retval == 0 else ("TIMEOUT" if retval == -50 else f"FAILED({retval})")
        print(f"  - {apkName}: {status}")
    print(f"{'='*60}\n")
    
    return 0 if success_count == len(results) else 1

def main():
    configs = parseMainParam();
    
    # If no APK specified, try to use APK directory from config
    if configs.APK_NAME == "":
        if "apk_directory" in CONFIG and pathExists(CONFIG["apk_directory"]):
            print(f"[INFO] No APK specified, using directory from config: {CONFIG['apk_directory']}")
            return runGatorOnAllAPKsInDirectory(
                CONFIG["apk_directory"],
                configs.GATOR_OPTIONS,
                configs.KEEP_DECODE,
                configs=configs
            )
        else:
            print("[ERROR] No APK file specified and no valid apk_directory in config")
            print("Usage: python runGatorOnApk.py <path_to_apk> [options]")
            print("   or: Set 'apk_directory' in config file to analyze all APKs in that directory")
            return -1
    
    return runGatorOnAPKDirect(configs.APK_NAME,\
     configs.GATOR_OPTIONS,\
     configs.KEEP_DECODE, configs = configs)

if __name__ == '__main__':
    main()
