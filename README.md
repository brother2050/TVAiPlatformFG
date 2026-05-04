# TVAiPlatformFG


 待关注项（非错误）
项目
说明
状态
18 个组件未被 views 引用
Character/Editor/Preview/Settings/Timeline 下的组件，views 用内联实现替代
已确认：views 使用内联实现，这些组件作为备选/可复用单元保留
BgmAdjust 无 API 调用
后端有 BGM 端点，前端 editor.ts 缺少 BGM 方法
已修复：添加了完整的 BGM API 调用（生成、上传、混音）
后端 editor.py 全部是 stub
14 个端点均返回 mock 数据，标注了 TODO
已修复：集成 ComfyUI、ChatTTS、ImageEditorService，添加 SFX 内置库
后端 production.py 部分 stub
5 个端点中 3 个有 TODO
已修复：完善了生产管线逻辑，添加了 stage 执行框架
大 chunk 警告
element-plus 961KB，建议后续 code-split
已修复：配置了 Vite manualChunks，按功能分拆 vendor chunk

