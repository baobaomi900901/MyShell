  #   switch ($action) {
  #       "lang-cn" {
  #           code D:\Code\aom\KingAutomate\Res\chinese.json
  #           Write-Host "打开 CN 语言包" -ForegroundColor Blue
  #       }
  #       "lang-en" {
  #           code D:\Code\aom\KingAutomate\Res\english.json
  #           Write-Host "打开 EN 语言包" -ForegroundColor Blue
  #       }
  #       "Error-message" {
  #           code D:\Code\aom\VueCodeBase\vue-king-automate\public\js\errorPatterns.js
  #           Write-Host "打开 错误信息" -ForegroundColor Blue
  #       }
  #       "Alias" {
  #           code D:\Code\aom\KingAutomate\Res\FunctionSetting.json
  #           Write-Host "打开 函数别名与设置" -ForegroundColor Blue    
  #       }
  #       default {
  #           Write-Host "使用方法:" -ForegroundColor Blue
  #           Write-Host "  code_ lang-cn       # 打开 CN 语言包" -ForegroundColor Yellow
  #           Write-Host "  code_ lang-en       # 打开 EN 语言包" -ForegroundColor Yellow
  #           Write-Host "  code_ Error-message # 打开 错误信息" -ForegroundColor Yellow
  #           Write-Host "  code_ Alias         # 打开 函数别名与设置" -ForegroundColor Yellow
  #       }
  # }

code_ {
    case "$1" in
    lang-cn)
        code ~/Documents/金智维/Code/aom/KingAutomate/Res/chinese.json
        echo "打开 CN 语言包"
        ;;

    lang-en)
        code ~/Documents/金智维/Code/aom/KingAutomate/Res/english.json
        echo "打开 EN 语言包"
        ;;

    Error-message)
        code ~/Documents/金智维/Code/aom/VueCodeBase/vue-king-automate/public/js/errorPatterns.js
        echo "打开 错误信息"
        ;;

    Alias)
        code ~/Documents/金智维/Code/aom/KingAutomate/Res/FunctionSetting.json
        echo "打开 函数别名与设置"
        ;;

    *)
        echo -e "${c_b}使用方法:${c_x}"
        echo -e "${c_y}  code_ lang-cn       # 打开 CN 语言包${c_x}"
        echo -e "${c_y}  code_ lang-en       # 打开 EN 语言包${c_x}"
        echo -e "${c_y}  code_ Error-message # 打开 错误信息${c_x}"
        echo -e "${c_y}  code_ Alias         # 打开 函数别名与设置${c_x}"
        ;;
    esac
}