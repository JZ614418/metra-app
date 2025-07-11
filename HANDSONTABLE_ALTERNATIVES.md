# Handsontable 开源替代方案

## 🎯 推荐：AG-Grid Community Edition

我们选择 **AG-Grid Community Edition** 作为 Handsontable 的替代方案。

### 为什么选择 AG-Grid？

1. **功能丰富**：提供了 Metra DFE 需要的所有功能
   - ✅ 单元格编辑
   - ✅ 数据验证
   - ✅ CSV 导入/导出
   - ✅ 大数据量支持
   - ✅ 自定义编辑器
   - ✅ 复制/粘贴

2. **性能优秀**：虚拟滚动，可处理百万级数据

3. **完全免费**：社区版 MIT 许可证，无需付费

4. **易于集成**：与 React 完美配合

### 安装步骤

```bash
cd metra-ai-factory-main
npm install ag-grid-community ag-grid-react
```

### 使用示例

已创建 `DataGridEditor.tsx` 组件，包含：
- 数据编辑功能
- CSV 导入/导出
- 行的添加/删除
- 数据验证
- 自适应列宽

### 在 DataEngine 中使用

```tsx
import { DataGridEditor } from './DataGridEditor';

// 在 DataEngine 组件中
<DataGridEditor
  initialData={processedData}
  onDataChange={handleDataUpdate}
  taskType={task.type}
/>
```

### AG-Grid vs Handsontable 功能对比

| 功能 | Handsontable Pro | AG-Grid Community |
|-----|------------------|-------------------|
| 基础编辑 | ✅ | ✅ |
| 数据验证 | ✅ | ✅ |
| CSV 导出 | ✅ | ✅ |
| 自定义编辑器 | ✅ | ✅ |
| 虚拟滚动 | ✅ | ✅ |
| 公式计算 | ✅ | ❌ (需要自己实现) |
| 价格 | $750/开发者 | 免费 |

### 其他备选方案

如果 AG-Grid 不满足需求，还可以考虑：

1. **React Data Grid** - 更轻量
2. **Tanstack Table** - 更灵活但需要更多自定义
3. **Glide Data Grid** - Canvas 渲染，极高性能

### 迁移注意事项

从设计稿迁移到 AG-Grid：
1. 样式已适配 Metra 的灰色主题
2. 使用 `ag-theme-alpine` 主题
3. 可通过 CSS 变量自定义颜色

### 结论

AG-Grid Community Edition 完全能够满足 Metra DFE 的数据编辑需求，且无需支付许可费用。已创建的组件可以直接使用。 