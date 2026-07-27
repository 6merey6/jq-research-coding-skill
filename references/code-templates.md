# 代码模板

## 注入代码并执行 Cell

```javascript
// 新建 cell（新功能）或回填原 cell（修改已有代码）
() => {
  const iframe = document.querySelector('iframe');
  const J = iframe.contentWindow.Jupyter;
  if (J && J.notebook) {
    // 方式A: 新建 cell 在末尾
    const ncells = J.notebook.get_cells().length;
    J.notebook.insert_cell_at_index('code', ncells);
    const cells = J.notebook.get_cells();
    const newCell = cells[cells.length - 1];
    newCell.set_text(codeString);
    J.notebook.execute_cells([J.notebook.find_cell_index(newCell)]);
    return { cell_index: J.notebook.find_cell_index(newCell), executed: true };

    // 方式B: 回填已有 cell（修改代码时用）
    // const cells = J.notebook.get_cells();
    // cells[targetIndex].set_text(newCode);
    // J.notebook.execute_cells([targetIndex]);
  }
  return { error: 'Jupyter not available' };
}
```

## 读取 Cell 输出（完整不截断）

```javascript
() => {
  const iframe = document.querySelector('iframe');
  const J = iframe.contentWindow.Jupyter;
  if (J && J.notebook) {
    const cells = J.notebook.get_cells();
    const lastCell = cells[cells.length - 1];
    const idx = J.notebook.find_cell_index(lastCell);

    const errs = lastCell.element.find('.output_error');
    const err_full = errs.length ? errs.text().trim() : '(none)';

    const outs = lastCell.element.find('.output_subarea:not(.output_error)');
    let output_full = '';
    outs.each(function() {
      output_full += this.innerText || this.textContent || '';
      output_full += '\n';
    });
    output_full = output_full.trim() || '(none)';

    const prompt = lastCell.element.find('.input_prompt').text().trim();

    return { cell_index: idx, input_prompt: prompt, has_error: errs.length > 0, err_full, output_full };
  }
  return { error: 'Jupyter not available' };
}
```

## 删除 Cell

```javascript
() => {
  const iframe = document.querySelector('iframe');
  const J = iframe.contentWindow.Jupyter;
  if (J && J.notebook) {
    J.notebook.delete_cells([cellIndex]);
    return { deleted: true, remaining: J.notebook.get_cells().length };
  }
  return { error: 'no jupyter' };
}
```

## 读取所有 Cell 内容

```javascript
() => {
  const iframe = document.querySelector('iframe');
  const J = iframe.contentWindow.Jupyter;
  if (J && J.notebook) {
    const cells = J.notebook.get_cells();
    const result = cells.map((cell, i) => ({
      index: i,
      type: cell.cell_type,
      source: cell.get_text(),
      prompt: cell.element.find('.input_prompt').text().trim()
    }));
    return { ncells: cells.length, cells: result };
  }
  return { error: 'no jupyter' };
}
```

## 检查内存使用

```javascript
// 方式A: snapshot 中直接看 "内存使用 XXXM/1.0G"
// 方式B: evaluate_script 读取
() => {
  const iframe = document.querySelector('iframe');
  const doc = iframe.contentDocument || iframe.contentWindow.document;
  // 在 toolbar 区域搜索内存按钮
  const allButtons = doc.querySelectorAll('button');
  for (const btn of allButtons) {
    const text = btn.textContent || '';
    if (text.includes('内存使用')) {
      const match = text.match(/(\d+)M\/([\d.]+)G/);
      if (match) {
        const used = parseInt(match[1]);
        const total = parseFloat(match[2]) * 1024;
        return { used_mb: used, total_mb: total, pct: (used/total*100).toFixed(1) + '%' };
      }
    }
  }
  return { error: 'memory indicator not found' };
}
```
