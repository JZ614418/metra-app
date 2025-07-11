import React, { useState, useCallback, useMemo } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent, CellValueChangedEvent } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Download, Upload, Plus, Trash2 } from 'lucide-react';

interface DataRow {
  id: string;
  content: string;
  label: string;
  source: string;
  confidence: number;
  [key: string]: any;
}

interface DataGridEditorProps {
  initialData?: DataRow[];
  onDataChange?: (data: DataRow[]) => void;
  taskType?: string;
}

export const DataGridEditor: React.FC<DataGridEditorProps> = ({
  initialData = [],
  onDataChange,
  taskType = 'text_classification'
}) => {
  const [rowData, setRowData] = useState<DataRow[]>(initialData);
  const [gridApi, setGridApi] = useState<any>(null);

  // Define columns based on task type
  const columnDefs = useMemo<ColDef[]>(() => {
    const baseColumns: ColDef[] = [
      {
        field: 'content',
        headerName: 'Content',
        flex: 2,
        editable: true,
        cellEditor: 'agLargeTextCellEditor',
        cellEditorPopup: true,
        cellEditorParams: {
          maxLength: 1000,
          rows: 10,
          cols: 50
        }
      },
      {
        field: 'label',
        headerName: 'Label',
        flex: 1,
        editable: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: {
          values: ['positive', 'negative', 'neutral'] // Dynamic based on task
        }
      },
      {
        field: 'source',
        headerName: 'Source',
        flex: 1,
        editable: false
      },
      {
        field: 'confidence',
        headerName: 'Confidence',
        width: 120,
        editable: true,
        valueFormatter: params => params.value ? `${(params.value * 100).toFixed(1)}%` : '',
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          max: 1,
          precision: 2
        }
      }
    ];

    return baseColumns;
  }, [taskType]);

  const defaultColDef = useMemo<ColDef>(() => ({
    sortable: true,
    filter: true,
    resizable: true,
    menuTabs: ['filterMenuTab'],
  }), []);

  const onGridReady = useCallback((params: GridReadyEvent) => {
    setGridApi(params.api);
  }, []);

  const onCellValueChanged = useCallback((event: CellValueChangedEvent) => {
    const updatedData = [];
    gridApi.forEachNode(node => updatedData.push(node.data));
    setRowData(updatedData);
    onDataChange?.(updatedData);
  }, [gridApi, onDataChange]);

  const addNewRow = useCallback(() => {
    const newRow: DataRow = {
      id: `row_${Date.now()}`,
      content: '',
      label: '',
      source: 'manual',
      confidence: 1.0
    };
    const updatedData = [...rowData, newRow];
    setRowData(updatedData);
    onDataChange?.(updatedData);
  }, [rowData, onDataChange]);

  const deleteSelectedRows = useCallback(() => {
    const selectedRows = gridApi.getSelectedRows();
    const updatedData = rowData.filter(row => !selectedRows.includes(row));
    setRowData(updatedData);
    onDataChange?.(updatedData);
  }, [gridApi, rowData, onDataChange]);

  const exportData = useCallback(() => {
    gridApi.exportDataAsCsv({
      fileName: `metra_data_${Date.now()}.csv`
    });
  }, [gridApi]);

  const importData = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      // Parse CSV and update rowData
      // This is a simplified example - you'd want proper CSV parsing
      console.log('Import CSV:', e.target?.result);
    };
    reader.readAsText(file);
  }, []);

  return (
    <Card className="p-4">
      <div className="mb-4 flex justify-between items-center">
        <h3 className="text-lg font-semibold">Data Editor</h3>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={addNewRow}
          >
            <Plus className="w-4 h-4 mr-1" />
            Add Row
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={deleteSelectedRows}
            disabled={!gridApi?.getSelectedRows()?.length}
          >
            <Trash2 className="w-4 h-4 mr-1" />
            Delete
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={exportData}
          >
            <Download className="w-4 h-4 mr-1" />
            Export
          </Button>
          <label>
            <Button
              variant="outline"
              size="sm"
              asChild
            >
              <span>
                <Upload className="w-4 h-4 mr-1" />
                Import
              </span>
            </Button>
            <input
              type="file"
              accept=".csv"
              onChange={importData}
              className="hidden"
            />
          </label>
        </div>
      </div>

      <div className="ag-theme-alpine" style={{ height: '500px', width: '100%' }}>
        <AgGridReact
          rowData={rowData}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onGridReady={onGridReady}
          onCellValueChanged={onCellValueChanged}
          rowSelection="multiple"
          animateRows={true}
          pagination={true}
          paginationPageSize={20}
          enableCellTextSelection={true}
          ensureDomOrder={true}
        />
      </div>

      <div className="mt-4 text-sm text-gray-500">
        {rowData.length} rows • Click cells to edit • Use Shift+Click to select multiple rows
      </div>
    </Card>
  );
}; 