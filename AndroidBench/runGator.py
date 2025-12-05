# 禁止生成 __pycache__ 
import sys
sys.dont_write_bytecode = True

import os
import json, subprocess, glob
import runGatorOnApk as runApk

PROJ_TYPE_APK=0
PROJ_TYPE_ECLIPSE=1
PROJ_TYPE_STUDIO=2
PROJ_TYPE_UNKNOWN=3

class SootGlobalConfig:
    GatorRoot=""
    ADKLocation=""
    AndroidBenchLocation=""
    CurrentWorkingDir=""
    ConfigFile=""
    OutputFolder=""
    jsonData=""
    externalSootCMD=""
    gatorDebugCodeList=[]
    gatorClient=""
    bResolveContext = True
    bSilent = False
    bDebug = False
    bExact = False
    pList = []
    jsonBASE_DIR=""
    jsonBASE_PARAM=""
    jsonBASE_CLIENT=""
    jsonBASE_CLIENT_PARAM=""
    paramBASE_DIR=""
    paramBASE_PARAM=""
    paramBASE_CLIENT=""
    paramBASE_CLIENT_PARAM=""
    projList = []
    AppPath=""
    AppAPILevel=""

class ProjectS:
    def __init__(
    self,
    projName,
    projPath,
    projAPI,
    projZipFile,
    projExtraLib,
    projParam,
    projClient,
    projClientParam):
        self.name = projName
        self.path = projPath
        self.API = projAPI
        self.zip = projZipFile
        self.extraLib = projExtraLib
        self.param = projParam
        self.client = projClient
        self.clientParam = projClientParam
        pass

    def __str__(self):
        curLine = "Name: {0}\nPath: {1}\nAPI Level: {2}\nZIP:{3}\nExtraLib:{4}\nParam:{5}\nClient:{6}\nClientParam:{7}\n".format(\
        self.name, self.path, self.API, self.zip, self.extraLib, self. param, self.client, self.clientParam)
        return curLine
        pass

    def doUnzip(self):
        print("Unzipping: " + self.zip)
        subprocess.call("unzip " + self.zip, shell=True)
        pass

    def execute(self):
        configFile = SootGlobalConfig.ConfigFile
        if configFile != "":
            # Extract only the filename without path (e.g., "apv/config.json" -> "config")
            baseName = os.path.basename(configFile)
            dirName = baseName[:baseName.find('.')]
        else:
            dirName = "output"
        pathName = SootGlobalConfig.CurrentWorkingDir + "/" + dirName
        if not os.path.exists(pathName):
            os.mkdir(pathName)
        if self.zip != "":
            #May Need to firstly unzip
            pcwd = os.getcwd()
            lastSlash = len(self.zip) - 1
            while lastSlash >= 0 and self.zip[lastSlash] == '/':
                lastSlash -= 1;
            while lastSlash >= 0 and self.zip[lastSlash] != '/':
                lastSlash -= 1;
            if lastSlash <= 0:
                print("Path information Error in " + self.__str__())
                sys.exit(-1)
            parPath = self.zip[:lastSlash]
            os.chdir(parPath)
            if not os.path.exists(self.path):
                self.doUnzip()
            os.chdir(pcwd)
            pass
        pcwd = os.getcwd();
        os.chdir(pathName);
        GatorOptions=""
        if self.client != '':
            GatorOptions = '{0} -client {1} {2}'.format(\
            self.param, self.client, self.clientParam)

        else:
            GatorOptions = self.param
        appType = determineProjectType(self.path)
        if appType == PROJ_TYPE_ECLIPSE:
            # It is an eclipse project
            manifestPath = self.path + "/AndroidManifest.xml"
            (classPath, resPath, depLibs) = parseEclipseProject(self.path)
            invokeGatorOnProject(projPath = self.path,\
                                resPath = resPath,\
                                manifestPath = manifestPath,\
                                classPath = classPath,\
                                apiLevel = self.API,\
                                extraLib = depLibs,\
                                benchmarkName = self.name,\
                                options = GatorOptions)
            pass
        elif appType == PROJ_TYPE_STUDIO:
            # It is an Android Studio project
            manifestPath = self.path + "/app/src/main/AndroidManifest.xml"
            resPath = self.path + "/app/build/intermediates/res/merged/debug"
            classPath = self.path + "/app/build/intermediates/classes/debug"
            invokeGatorOnProject(projPath = self.path,\
                                resPath = resPath,\
                                manifestPath = manifestPath,\
                                classPath = classPath,\
                                apiLevel = self.API,\
                                extraLib = self.extraLib,\
                                benchmarkName = self.name,\
                                options = GatorOptions)
            pass
        elif appType == PROJ_TYPE_APK:
            # It is an apk
            runApk.runGatorOnAPKDirect(self.path, GatorOptions.split(), False)
            pass
        else:
            fatalError("Unknown project type, abort!")
        os.chdir(pcwd)
        print(self.name + " FINISHED")

def parseEclipseProject(eclipseProjDir):
    depLibs = ""
    classPath = os.path.join(eclipseProjDir, "bin", "classes")
    resPath = os.path.join(eclipseProjDir, "res")
    #Open the project.properties file
    projPropPath = os.path.join(eclipseProjDir, "project.properties")
    projProp = open(projPropPath, "r")
    projLines = projProp.readlines()
    projProp.close()
    for curLine in projLines:
        if curLine.startswith("android.library.reference"):
            #There is a library class declearation
            pathStr = curLine[curLine.find("=") + 1:]
            pathStr = pathStr.strip()
            if os.path.isabs(pathStr):
                #It is an absolute path
                depLibs += os.pathsep + os.path.join(pathStr, "bin", "classes")
                resPath += os.pathsep + os.path.join(pathStr, "res")
            else:
                #It is a relative path
                depLibs += os.pathsep + os.path.join(eclipseProjDir, pathStr, "bin", "classes")
                resPath += os.pathsep + os.path.join(eclipseProjDir, pathStr, "res")
    if depLibs.startswith(os.pathsep):
        depLibs = depLibs[len(os.pathsep):]
    return (classPath, resPath, depLibs)

def pathExists(pathName):
    if os.access(pathName, os.F_OK):
        return True
    return False;

def extractLibsFromPath(pathName):
    if not pathExists(pathName):
        return ""
        pass
    fileList = glob.glob(pathName+"/*.jar")
    if len(fileList) == 0:
        return ""
    ret = ""
    for item in fileList:
        ret += os.pathsep + item
    return ret;

def invokeGatorOnProject(\
                projPath,
                resPath,
                manifestPath,
                classPath,
                apiLevel,
                extraLib,
                benchmarkName,
                options):
    ''''''
    SootAndroidLocation = os.path.normpath(os.path.join(SootGlobalConfig.GatorRoot, "SootAndroid"))
    sdkLocation = os.path.normpath(SootGlobalConfig.ADKLocation)
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
        GoogleAPIDir = os.path.normpath(os.path.join(sdkLocation, 
            "add-ons", "addon-google_apis-google-" + sLevelNum))
        if not pathExists(GoogleAPIDir) :
            print("Google API Level:" + sLevelNum + "Not installed!")
            sys.exit(-1);
        GoogleAPI = extractLibsFromPath(os.path.join(GoogleAPIDir, "libs"))
    PlatformAPIDir = os.path.normpath(os.path.join(sdkLocation,
            "platforms", "android-" + str(iLevelNum)))
    # 强制包含 sootclasses.jar
    sootJarPath = os.path.normpath(os.path.join(SootAndroidLocation, "lib", "sootclasses.jar"))
    ClassPathJar = extractLibsFromPath(os.path.join(SootAndroidLocation, "lib"))
    ClassPathJar = os.path.normpath(os.path.join(SootAndroidLocation, "bin")) + os.pathsep + sootJarPath + ClassPathJar
    # 修正 classPath，确保不为空且路径存在
    if not classPath or not os.path.exists(classPath):
        classPath = os.path.normpath(os.path.join(SootAndroidLocation, "bin"))
    PlatformJar = os.path.normpath(os.path.join(sdkLocation, "platforms", "android-" + sLevelNum, "android.jar"))
    if bGoogleAPI:
        PlatformJar += GoogleAPI
    if iLevelNum >= 14:
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
        for lib in supportLibs:
            PlatformJar += os.pathsep + os.path.normpath(os.path.join(SootAndroidLocation, "deps", lib))
    if extraLib != None and extraLib != "":
        # extraLib 可能包含冒号分隔的路径列表，需要转换为当前系统的分隔符
        extraLibPaths = extraLib.replace(":", os.pathsep).split(os.pathsep)
        for libPath in extraLibPaths:
            if libPath.strip():
                PlatformJar += os.pathsep + os.path.normpath(libPath.strip())
    
    # 获取 JRE 路径和 Java 版本
    jreLib = ""
    javaVersion = 8  # 默认假设 Java 8
    
    # 检测 Java 版本
    try:
        versionOutput = subprocess.check_output(['java', '-version'], 
                                              stderr=subprocess.STDOUT,
                                              universal_newlines=True)
        # 解析版本号（例如 "18.0.2.1" 或 "1.8.0_xxx"）
        import re
        match = re.search(r'version "(\d+)\.(\d+)', versionOutput)
        if match:
            majorVer = int(match.group(1))
            if majorVer == 1:
                # 旧版本格式 "1.8.x"
                javaVersion = int(match.group(2))
            else:
                # 新版本格式 "9.x", "11.x", "18.x" 等
                javaVersion = majorVer
    except Exception as e:
        if SootGlobalConfig.bDebug:
            print("Warning: Could not detect Java version:", e)
    
    # 根据 Java 版本获取适当的库路径
    javaHome = os.environ.get("JAVA_HOME")
    if not javaHome:
        # 尝试从 java 命令推断
        try:
            javaCmd = subprocess.check_output(['where' if sys.platform == 'win32' else 'which', 'java'], 
                                            stderr=subprocess.STDOUT,
                                            universal_newlines=True).strip().split('\n')[0]
            javaHome = os.path.dirname(os.path.dirname(javaCmd))
        except Exception:
            pass
    
    if javaHome and javaVersion >= 9:
        # Java 9+ 使用模块系统，不需要 rt.jar
        # 我们将使用空的 jreLib，Soot 会自动处理
        jreLib = ""
        if SootGlobalConfig.bDebug:
            print(f"Detected Java {javaVersion}, using module system")
    elif javaHome:
        # Java 8 及以下，查找 rt.jar
        rtJar = os.path.join(javaHome, "jre", "lib", "rt.jar")
        if os.path.exists(rtJar):
            jreLib = rtJar
        else:
            # 某些 JDK 的 rt.jar 直接在 lib 目录
            rtJar = os.path.join(javaHome, "lib", "rt.jar")
            if os.path.exists(rtJar):
                jreLib = rtJar
        
        if SootGlobalConfig.bDebug:
            print(f"Detected Java {javaVersion}, rt.jar: {jreLib if jreLib else 'Not found'}")
    
    #Finished computing platform libraries
    callList = [\
                'java', \
                '-Xmx12G']\
    
    # 对于 Java 9+，设置模块相关选项和必需的系统属性
    if javaVersion >= 9:
        # Java 9+ 需要添加模块访问权限
        callList.extend([
            '--add-opens', 'java.base/java.lang=ALL-UNNAMED',
            '--add-opens', 'java.base/java.util=ALL-UNNAMED',
            '--add-opens', 'java.base/java.io=ALL-UNNAMED'
        ])
        # 设置 Soot 需要的系统属性（Java 9+ 中这些属性已被移除）
        callList.extend([
            '-Djava.class.path=' + ClassPathJar,
            '-Dsun.boot.class.path=',
            '-Djava.ext.dirs=',
            '-Djava.endorsed.dirs='
        ])
    elif jreLib:
        # 只在 Java 8 且有 rt.jar 时设置 sun.boot.class.path
        callList.extend(['-Dsun.boot.class.path=' + jreLib])
    
    callList.extend([\
                '-classpath', ClassPathJar, \
                'presto.android.Main'])
    
    # 只在 Java 8 且有 jreLib 时添加 -jre 参数
    if javaVersion < 9 and jreLib:
        callList.extend(['-jre', jreLib])
    
    # 添加其余参数
    callList.extend([\
                '-project', projPath,\
                '-android', PlatformJar,\
                '-sdkDir', sdkLocation,\
                '-classFiles', classPath, \
                '-resourcePath', resPath, \
                '-manifestFile', manifestPath,\
                '-apiLevel', "android-" + sLevelNum,\
                '-benchmarkName', benchmarkName,\
                '-guiAnalysis',
                '-listenerSpecFile', os.path.normpath(os.path.join(SootAndroidLocation, "listeners.xml")),\
                '-wtgSpecFile', os.path.normpath(os.path.join(SootAndroidLocation, 'wtg.xml'))])
    options = options.split()
    callList.extend(options);
    
    # 调试输出
    if SootGlobalConfig.bDebug:
        print("JRE Lib:", jreLib)
        print("Command:", ' '.join(callList))
    
    subprocess.call(callList)
    pass

def fatalError(str):
    print(str)
    sys.exit(1)
    pass

def waitForEnter():
    try:
        input("Press ENTER to continue")
    except:
        pass

def debugOutput():
    print("ConfigFile: "+ SootGlobalConfig.ConfigFile)
    print("GatorRoot: "+ SootGlobalConfig.GatorRoot)
    print("ADKLocation: "+ SootGlobalConfig.ADKLocation)
    print("CurrentWorkingDir: "+ SootGlobalConfig.CurrentWorkingDir)
    print("OutputFolder: "+ SootGlobalConfig.OutputFolder)
    print("Projects: ")
    for item in SootGlobalConfig.projList:
        print(item)


def parseSingleProject(key, curData):
    #Not a reserved Keyword
    baseDir = SootGlobalConfig.jsonBASE_DIR
    baseParam = SootGlobalConfig.jsonBASE_PARAM
    baseClient = SootGlobalConfig.jsonBASE_CLIENT
    baseClientParam = SootGlobalConfig.jsonBASE_CLIENT_PARAM
    curName = key
    curPath = ""
    curAPI = ""
    curZip = ""
    curExtraLib = ""
    curParam = ""
    curClient = ""
    curClientParam = ""
    if "abs-path" in curData and curData["abs-path"] != "":
        curPath = curData["abs-path"]
    elif "relative-path" in curData:
        curPath = baseDir + "/" + curData["relative-path"]
    else:
        fatalError("Error: Path is not defined in " + curName)

    if "api-level" in curData:
        curAPI = curData["api-level"]
    else:
        fatalError("Error: API Level is not defined " + curName)

    if "abs-zip-file" in curData and curData["abs-zip-file"] != "":
        curZip = curData["abs-zip-file"]
    elif "zip-file" in curData and curData["zip-file"] != "":
        curZip = baseDir + "/" + curData["zip-file"]

    if "extra-lib" in curData:
        curExtraLib = curData["extra-lib"]

    if "override-param" in curData and curData["override-param"] != "":
        curParam = curData["override-param"]
    elif "append-param" in curData:
        curParam = baseParam + ' ' + curData["append-param"]
    else:
        curParam = baseParam

    if "override-client" in curData and curData["override-client"] != "":
        curClient = curData["override-client"]
    else:
        curClient = baseClient

    if "override-client-param" in curData and curData["override-client-param"] != "":
        curClientParam = curData["override-client-param"]
    elif "append-client-param" in curData:
        curClientParam = baseClientParam + ' ' + curData["append-client-param"]
    else:
        curClientParam = baseClientParam

    curProj = ProjectS(\
      projName = curName,\
      projPath = curPath,\
      projAPI = curAPI,\
      projZipFile = curZip,\
      projExtraLib = curExtraLib,\
      projParam = curParam,\
      projClient = curClient,\
      projClientParam = curClientParam)
    SootGlobalConfig.projList.append(curProj)

def parseProjects(jsData):
    for key in jsData:
        #Reserved Keyword?
        if key == "BASE_DIR":
            SootGlobalConfig.jsonBASE_DIR = jsData[key].__str__()
            if len(SootGlobalConfig.paramBASE_DIR) != 0:
                SootGlobalConfig.jsonBASE_DIR = SootGlobalConfig.paramBASE_DIR
        elif key == "BASE_PARAM":
            SootGlobalConfig.jsonBASE_PARAM = jsData[key].__str__()
            if len(SootGlobalConfig.paramBASE_PARAM) != 0:
                SootGlobalConfig.jsonBASE_PARAM = SootGlobalConfig.paramBASE_PARAM
        elif key == "BASE_CLIENT":
            SootGlobalConfig.jsonBASE_CLIENT = jsData[key].__str__()
            if len(SootGlobalConfig.paramBASE_CLIENT) != 0:
                SootGlobalConfig.jsonBASE_CLIENT = SootGlobalConfig.paramBASE_CLIENT
        elif key == "BASE_CLIENT_PARAM":
            SootGlobalConfig.jsonBASE_CLIENT_PARAM = jsData[key].__str__()
            if len(SootGlobalConfig.paramBASE_CLIENT_PARAM) != 0:
                SootGlobalConfig.jsonBASE_CLIENT_PARAM = SootGlobalConfig.paramBASE_CLIENT_PARAM
        pass

    for key in jsData:
        if key == "BASE_DIR" or \
        key == "BASE_PARAM" or \
        key == "BASE_CLIENT" or \
        key == "BASE_CLIENT_PARAM":
            continue
        else:
            #Not a reserved Keyword
            curData = jsData[key]
            parseSingleProject(key, curData)

def loadJSON(fileName):
    global jsonData
    fileFD = None
    try:
        fileFD = open(fileName, "r")
    except:
        print("JSON configuration file open error! Abort.")
        sys.exit(0)

    jsonData = json.load(fileFD)
    #print(jsonData)
    return jsonData

def determinGatorRootAndSDKPath():
    gatorRoot = os.environ.get("GatorRoot")
    if gatorRoot != None:
        SootGlobalConfig.GatorRoot = gatorRoot
    else:
        curPath = os.getcwd()
        curPathNames = curPath.replace('\\', '/').split('/')
        lastDirName = "";
        for i in reversed(range(len(curPathNames))):
            if curPathNames[i] != '':
                lastDirName = curPathNames[i]
                break
            pass
        if lastDirName == "AndroidBench":
            SootGlobalConfig.GatorRoot = os.path.dirname(curPath)
            os.environ['GatorRoot'] = SootGlobalConfig.GatorRoot
        else:
            fatalError("GatorRoot environment variable is not defined")
    adkRoot = os.environ.get("ADK")
    if adkRoot != None:
        SootGlobalConfig.ADKLocation = adkRoot
    else:
        homeDir = os.environ.get("HOME")
        userProfile = os.environ.get("USERPROFILE")  # Windows 用户目录
        if homeDir == None and userProfile == None:
            fatalError("ADK environment variable is not defined")
        if homeDir == None:
            homeDir = userProfile
        if sys.platform == "linux2" or sys.platform == "linux":
            if pathExists(os.path.join(homeDir, "Android", "Sdk")):
                SootGlobalConfig.ADKLocation = os.path.join(homeDir, "Android", "Sdk")
            else:
                fatalError("ADK environment variable is not defined")
        elif sys.platform == "darwin":
            if pathExists(os.path.join(homeDir, "Library", "Android", "sdk")):
                SootGlobalConfig.ADKLocation = os.path.join(homeDir, "Library", "Android", "sdk")
            else:
                fatalError("ADK environment variable is not defined")
        elif sys.platform == "win32":
            # Windows 平台
            if pathExists(os.path.join(homeDir, "AppData", "Local", "Android", "Sdk")):
                SootGlobalConfig.ADKLocation = os.path.join(homeDir, "AppData", "Local", "Android", "Sdk")
            elif pathExists(os.path.join(homeDir, "Android", "Sdk")):
                SootGlobalConfig.ADKLocation = os.path.join(homeDir, "Android", "Sdk")
            else:
                fatalError("ADK environment variable is not defined")
        else:
            fatalError("ADK environment variable is not defined")
        os.environ['ADK'] = SootGlobalConfig.ADKLocation
        pass
    pass


def parseMainParam():
    determinGatorRootAndSDKPath()
    params = sys.argv
    gatorRoot = SootGlobalConfig.GatorRoot
    SootGlobalConfig.CurrentWorkingDir = os.getcwd()
    adkLocation = SootGlobalConfig.ADKLocation
    SootGlobalConfig.AndroidBenchLocation = SootGlobalConfig.GatorRoot + "/AndroidBench"
    i = 0;
    while (i < len(params) - 1):
        i += 1
        val = params[i]
        if val == '-j':
            i += 1
            SootGlobalConfig.ConfigFile = params[i]
            continue
        elif val == '-s':
            SootGlobalConfig.bSilent = True
            continue
        elif val == '-o':
            i += 1
            SootGlobalConfig.OutputFolder = params[i]
            continue
        elif val == '-p':
            i += 1
            SootGlobalConfig.pList.append(params[i])
            continue
        elif val == '-v':
            SootGlobalConfig.bDebug = True
            continue
        elif val == '--base_dir':
            i += 1
            SootGlobalConfig.paramBASE_DIR = params[i]
            continue
        elif val == '--base_param':
            i += 1
            SootGlobalConfig.paramBASE_PARAM = params[i]
            continue
        elif val == '--base_client':
            i += 1
            SootGlobalConfig.paramBASE_CLIENT = params[i]
            continue
        elif val == '--base_client_param':
            i += 1
            SootGlobalConfig.paramBASE_CLIENT_PARAM = params[i]
            continue
        elif val == '-e' or val == '--exact':
            SootGlobalConfig.bExact = True
            continue
        elif val == "-app":
            i += 1
            SootGlobalConfig.AppPath = params[i]
        elif val == "-applevel":
            i += 1
            SootGlobalConfig.AppAPILevel = params[i]
        pass
    if SootGlobalConfig.ConfigFile == "" and SootGlobalConfig.AppPath == "":
        fatalError("Config File undefined");
    if SootGlobalConfig.OutputFolder == "":
        SootGlobalConfig.OutputFolder = os.getcwd()

def determineProjectType(projectPath):
    if not pathExists(projectPath):
        fatalError("Project path does not exist")
    if projectPath[-4:] == ".apk":
        return PROJ_TYPE_APK
    #It is not a apk
    if not os.path.isdir(projectPath):
        return PROJ_TYPE_UNKNOWN
    #It is a dir
    fileList = os.listdir(projectPath)
    if ".project" in fileList and "AndroidManifest.xml" in fileList and ("build.gradle" not in fileList):
        return PROJ_TYPE_ECLIPSE
    if "project.properties" in fileList and "AndroidManifest.xml" in fileList and ("build.gradle" not in fileList):
        return PROJ_TYPE_ECLIPSE
    elif "build.gradle" in fileList and "gradlew" in fileList:
        return PROJ_TYPE_STUDIO
    else:
        return PROJ_TYPE_UNKNOWN

def runOnSingleApp():
    appType = determineProjectType(SootGlobalConfig.AppPath)
    if appType == PROJ_TYPE_APK:
        #It is an apk. Prepare Gator parameters.
        if SootGlobalConfig.paramBASE_CLIENT != "":
            GatorParam = "{0} -client {1} {2}".format(SootGlobalConfig.paramBASE_PARAM, \
            SootGlobalConfig.paramBASE_CLIENT, SootGlobalConfig.paramBASE_CLIENT_PARAM)
        else:
            GatorParam = SootGlobalConfig.paramBASE_PARAM
        runApk.runGatorOnAPKDirect(SootGlobalConfig.AppPath, GatorParam.split(), False)
        return
    elif appType == PROJ_TYPE_STUDIO or appType == PROJ_TYPE_ECLIPSE:
        #It is an Android Studio project or an eclipse project
        if SootGlobalConfig.AppAPILevel == "":
            SootGlobalConfig.AppAPILevel = "google-23"
        projectName = SootGlobalConfig.AppPath.split("/")[-1]
        if projectName.strip() == "":
            projectName = "singleProject"
        curProj = ProjectS(\
            projName = projectName,\
            projPath = SootGlobalConfig.AppPath,\
            projAPI = SootGlobalConfig.AppAPILevel,\
            projZipFile = "",\
            projExtraLib = "",\
            projParam = SootGlobalConfig.paramBASE_PARAM,\
            projClient = SootGlobalConfig.paramBASE_CLIENT,\
            projClientParam = SootGlobalConfig.paramBASE_CLIENT_PARAM)
        curProj.execute()
        return
    elif appType == PROJ_TYPE_UNKNOWN:
        fatalError("Unknow project type, abort!")
        return
    pass

def main():
    parseMainParam()
    if SootGlobalConfig.AppPath != "":
        runOnSingleApp()
        return

    print("Loading " + SootGlobalConfig.ConfigFile)
    jsData = loadJSON(SootGlobalConfig.ConfigFile)
    parseProjects(jsData)
    if SootGlobalConfig.bDebug:
        debugOutput()
    if len(SootGlobalConfig.pList) > 0:
        for curStr in SootGlobalConfig.pList:
            for curItem in SootGlobalConfig.projList:
                if (SootGlobalConfig.bExact and curStr == curItem.name) or ((not SootGlobalConfig.bExact) and curStr in curItem.name ):
                    curItem.execute()
    else:
        for curItem in SootGlobalConfig.projList:
            curItem.execute()
    print("All Done!")
    pass


if __name__ == "__main__":
    main()
    pass
