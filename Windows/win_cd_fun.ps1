# #项目
function cd_ {
    param (
        [Parameter(Position = 0)]
        [ArgumentCompleter({
            param ($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
            $validActions = @('aom', 'vcl', 'litebuild', 'liteapp', 'liteweb', 'sb8', 'kswux')
            $validActions -like "$wordToComplete*"
        })]
        [string]$action
    )

    switch ($action) {
        "aom" {
            cd D:\Code\aom
            Write-Host "Executed: cd D:\Code\aom"
        }
        "vcl" {
            cd D:\Code\vcl
            Write-Host "Executed: cd D:\Code\vcl"
        }
        "litebuild" {
            cd D:\Code\aom\KingAutomate\Build\Build
            Write-Host "Executed: cd D:\Code\aom\KingAutomate\Build\Build"
        }
        "liteapp" {
            cd D:\Code\aom\KingAutomate
            Write-Host "Executed: cd D:\Code\aom\KingAutomate"
        }
        "liteweb" {
            cd D:\Code\aom\VueCodeBase\vue-king-automate
            Write-Host "Executed: cd D:\Code\aom\VueCodeBase\vue-king-automate"
        }
        "sb8" {
            cd D:\Code\storybook8
            Write-Host "Executed: cd D:\Code\storybook8"
        }
        "kswux" {
            cd D:\Code\storybook8\kswux
            Write-Host "Executed: cd D:\Code\storybook8\kswux"
        }
        "hotkey" {
            cd D:\Program Files\AutoHotkey\MyHotkey
            Write-Host "Executed: cd D:\Program Files\AutoHotkey\MyHotkey"
        }
        default {
            Write-Host "使用方法:" -ForegroundColor Blue
            Write-Host "  cd_ aom        # 研发一部代码" -ForegroundColor Yellow
            Write-Host "  cd_ vcl        # 工具库" -ForegroundColor Yellow
            Write-Host "  cd_ litebuild  # lite build文件夹" -ForegroundColor Yellow   
            Write-Host "  cd_ liteapp    # lite 后端代码" -ForegroundColor Yellow
            Write-Host "  cd_ liteweb    # lite 前端代码" -ForegroundColor Yellow
            Write-Host "  cd_ sb8        # storybook8" -ForegroundColor Yellow
            Write-Host "  cd_ kswux      # KSW组件库" -ForegroundColor Yellow
            Write-Host "  cd_ hotkey     # AHK热键脚本" -ForegroundColor Yellow
        }
    }
}