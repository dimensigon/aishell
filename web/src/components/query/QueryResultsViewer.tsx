import React, { useState, useMemo } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  ToggleButtonGroup,
  ToggleButton,
  IconButton,
  Typography,
} from '@mui/material';
import {
  TableChart,
  Code,
  BarChart,
  Download,
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import api from '@services/api';
import { ChartViewer } from '@components/visualizations/ChartViewer';
import type { QueryResult } from '@types/index';

interface Props {
  result: QueryResult;
}

type ViewMode = 'table' | 'json' | 'chart';

export const QueryResultsViewer: React.FC<Props> = ({ result }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  const paginatedRows = useMemo(() => {
    const start = page * rowsPerPage;
    const end = start + rowsPerPage;
    return result.rows.slice(start, end);
  }, [result.rows, page, rowsPerPage]);

  const handleExport = async (format: 'csv' | 'json' | 'xlsx') => {
    try {
      const blob = await api.exportData(format, result);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `query_result_${Date.now()}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Export failed');
    }
  };

  return (
    <Box sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Box>
          <Typography variant="body2" color="text.secondary">
            {result.rowCount} rows in {result.executionTime}ms
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(_, value) => value && setViewMode(value)}
            size="small"
          >
            <ToggleButton value="table">
              <TableChart />
            </ToggleButton>
            <ToggleButton value="json">
              <Code />
            </ToggleButton>
            <ToggleButton value="chart">
              <BarChart />
            </ToggleButton>
          </ToggleButtonGroup>

          <IconButton
            size="small"
            onClick={() => handleExport('csv')}
            title="Export as CSV"
          >
            <Download />
          </IconButton>
        </Box>
      </Box>

      {/* Content */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        {viewMode === 'table' && (
          <>
            <TableContainer component={Paper} sx={{ maxHeight: 'calc(100% - 60px)' }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    {result.columns.map((col) => (
                      <TableCell key={col} sx={{ fontWeight: 'bold' }}>
                        {col}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedRows.map((row, idx) => (
                    <TableRow key={idx} hover>
                      {result.columns.map((col) => (
                        <TableCell key={col}>
                          {formatValue(row[col])}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={result.rowCount}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={(_, newPage) => setPage(newPage)}
              onRowsPerPageChange={(e) => {
                setRowsPerPage(parseInt(e.target.value, 10));
                setPage(0);
              }}
            />
          </>
        )}

        {viewMode === 'json' && (
          <Paper sx={{ p: 2, height: '100%', overflow: 'auto' }}>
            <pre style={{ margin: 0, fontSize: '0.875rem' }}>
              {JSON.stringify(result.rows, null, 2)}
            </pre>
          </Paper>
        )}

        {viewMode === 'chart' && (
          <ChartViewer data={result.rows} columns={result.columns} />
        )}
      </Box>
    </Box>
  );
};

function formatValue(value: any): string {
  if (value === null || value === undefined) {
    return '-';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  return String(value);
}
