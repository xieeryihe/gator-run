export GatorRoot=C:\Code\experiment\Gator
export ADK=D:\AndroidSDK

运行前准备：
- 如文档所说，下载ant并编译
- 配置配置ADK



1.通过py脚本直接分析app

python runGator.py -j cgo.json -p apv

目标app的配置在cgo.json中，其余配置文件没有尝试。

apv是一个 APP，直接通过源码分析。
为了使代码可以运行，通过copilot做了大量修改，主要包括
- runGator.py和java代码中中路径拼接问题，window适配问题（本代码在win10上运行，其余系统不保证）
- 其它一些小修小补（具体忘了）

分析的输出类似
```txt
Loading cgo.json
Soot started on Fri Dec 05 14:44:06 CST 2025
Warning: com.android.internal.widget.WeightedLinearLayout is a phantom class!
Warning: com.android.internal.R$menu is a phantom class!Warning: com.android.internal.view.menu.IconMenuView is 
a phantom class!
Warning: com.android.internal.widget.DigitalClock is a phantom class!
Warning: com.android.internal.app.AlertController$RecycleListView is a phantom class!
Warning: com.android.internal.widget.LinearLayoutWithDefaultTouchRecepient is a phantom class!
Warning: com.android.internal.view.menu.IconMenuItemView is a phantom class!
Warning: android.app.SearchDialog$SearchAutoComplete is 
a phantom class!
Warning: android.R$menu is a phantom class!
Warning: android.widget.NumberPicker is a phantom class!Warning: com.android.internal.widget.LockPatternView is 
a phantom class!
Warning: android.widget.DateTimeView is a phantom class!Warning: com.android.internal.view.menu.ListMenuItemView is a phantom class!
Warning: com.android.internal.widget.PasswordEntryKeyboardView is a phantom class!
Warning: com.android.internal.R$layout is a phantom class!
Warning: android.app.SearchDialog$SearchBar is a phantom class!
Warning: com.android.internal.widget.DialogTitle is a phantom class!
Warning: android.inputmethodservice.ExtractButton is a phantom class!
Warning: android.widget.NumberPickerButton is a phantom 
class!
Warning: com.android.internal.R$string is a phantom class!
Warning: com.android.internal.view.menu.ExpandedMenuView is a phantom class!
Warning: com.android.internal.policy.impl.RecentApplicationsBackground is a phantom class!
Warning: com.android.internal.widget.SlidingTab is a phantom class!
Warning: com.android.internal.R$id is a phantom class!  
Warning: java.lang.invoke.LambdaMetafactory is a phantom class!
Warning: java.lang.ref.Finalizer is a phantom class!    
Warning: android.view.MenuItem$OnActionExpandListener is a phantom class!
[Stat] #Classes: 801, #AppClasses: 68
[HIER] All classes: 801 [App: 68, Lib : 706, Phantom: 27]
[HIER] Activities: 4, lib activities: 4
[HIER] App views: 1, Lib views: 38
[HIER] App Dialogs: 0, Lib Dialogs: 3
[DEBUG] android.R$menu is phantom!
Warning: android.view.NumberPicker is a phantom class!  
Warning: android.view.NumberPickerButton is a phantom class!
[GUIAnalysis] Start
[XML] Layout Ids: 116, Menu Ids: 0, Widget Ids: 577, String Ids: 83
[XML] MainActivity: cx.hell.android.pdfview.ChooseFileActivity
[GUIAnalysis] End: 0.290891 sec
Soot stopped on Fri Dec 05 14:44:08 CST 2025
[DEBUG] Debug file at `C:\Users\wyc\AppData\Local\Temp\null-DEBUG-12038499223689951525.txt'.
apv FINISHED
Press ENTER to continue--base_dir $GatorRoot/AndroidBench
```



