# SZ_3D iPhone 工程

在 macOS 上安装 Xcode 和 XcodeGen，从仓库根目录执行 `sh ios/prepare-xcode.sh`，然后用 Xcode 打开 `ios/SZ3D.xcodeproj`。脚本会把与桌面版相同的离线图集放进应用，运行时从应用本地读取。

连接 iPhone，在 Xcode 的 Signing & Capabilities 中选择你的 Apple 签名团队。如果团队无法注册 `com.sz3d.atlas`，使用该团队可用的唯一 Bundle ID。选中你的 iPhone 并运行，可在实机上检查 WebGL 渲染、旋转缩放和建筑搜索。

要给指定设备下载并安装 IPA，使用 Apple Developer 团队登记设备，再从 Xcode Archive 导出适用于这些设备的签名包。面向更多用户可通过 TestFlight 或 App Store 分发。通过 GitHub 下载文件后能否安装，取决于 Apple 签名和对应的分发方式。

此工程需要 macOS 构建和 iPhone 实机验证。

仓库的「Build native iPhone app」工作流可在 GitHub 的 macOS runner 上编译真机版本，并生成待签名的 IPA。该产物用于后续个人签名或开发测试，iPhone 会拒绝直接安装未经签名的包。个人自用时可在 Windows 上用支持 Apple 个人签名的工具通过 USB 安装，需要本人登录 Apple 账户。免费个人签名通常每 7 天续签一次。要提供面向他人的下载入口，可使用 TestFlight 分发，或给已登记的设备导出 Ad Hoc 包。

## 面向公众发布

在 App Store Connect 创建 App 记录后，使用已加入 Apple Developer Program 的发布团队选择 App Store Connect 分发签名。在签名环境中用 Xcode Archive 上传构建。用 TestFlight 做真机测试，再提交 App Review。审核通过并发布之后，将 App Store 下载链接写入 GitHub 发布页。截屏应来自实际运行的 iPhone 环境。
