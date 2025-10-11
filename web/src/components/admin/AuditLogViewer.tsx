import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Collapse,
} from '@mui/material';
import { ExpandMore, ExpandLess } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import api from '@services/api';
import type { AuditLog } from '@types/index';

export const AuditLogViewer: React.FC = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [actionFilter, setActionFilter] = useState('');
  const [searchUser, setSearchUser] = useState('');
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const { data: logsData, isLoading } = useQuery({
    queryKey: ['auditLogs', page, rowsPerPage, actionFilter, searchUser],
    queryFn: async () => {
      const response = await api.getAuditLogs(
        searchUser || undefined,
        actionFilter || undefined,
        page + 1,
        rowsPerPage
      );
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const getActionColor = (action: string) => {
    switch (action) {
      case 'login':
      case 'register':
        return 'success';
      case 'logout':
        return 'default';
      case 'create':
        return 'primary';
      case 'update':
        return 'info';
      case 'delete':
        return 'error';
      case 'execute':
        return 'warning';
      default:
        return 'default';
    }
  };

  const handleRowClick = (logId: string) => {
    setExpandedRow(expandedRow === logId ? null : logId);
  };

  if (isLoading) {
    return <Typography>Loading audit logs...</Typography>;
  }

  const logs = logsData?.items || [];
  const total = logsData?.total || 0;

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3 }}>
        Audit Logs
      </Typography>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            label="Search User"
            variant="outlined"
            size="small"
            value={searchUser}
            onChange={(e) => setSearchUser(e.target.value)}
            sx={{ flex: 1 }}
          />

          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Action</InputLabel>
            <Select
              value={actionFilter}
              label="Action"
              onChange={(e) => setActionFilter(e.target.value)}
            >
              <MenuItem value="">All Actions</MenuItem>
              <MenuItem value="login">Login</MenuItem>
              <MenuItem value="logout">Logout</MenuItem>
              <MenuItem value="register">Register</MenuItem>
              <MenuItem value="create">Create</MenuItem>
              <MenuItem value="update">Update</MenuItem>
              <MenuItem value="delete">Delete</MenuItem>
              <MenuItem value="execute">Execute</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Paper>

      {/* Logs Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>User</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Resource</TableCell>
              <TableCell>IP Address</TableCell>
              <TableCell width={50}></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs.map((log: AuditLog) => (
              <React.Fragment key={log.id}>
                <TableRow
                  hover
                  onClick={() => handleRowClick(log.id)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell>
                    {new Date(log.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell>{log.username}</TableCell>
                  <TableCell>
                    <Chip
                      label={log.action.toUpperCase()}
                      color={getActionColor(log.action)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{log.resource}</TableCell>
                  <TableCell>{log.ipAddress || '-'}</TableCell>
                  <TableCell>
                    <IconButton size="small">
                      {expandedRow === log.id ? <ExpandLess /> : <ExpandMore />}
                    </IconButton>
                  </TableCell>
                </TableRow>

                <TableRow>
                  <TableCell colSpan={6} sx={{ py: 0 }}>
                    <Collapse in={expandedRow === log.id} timeout="auto" unmountOnExit>
                      <Box sx={{ p: 2, bgcolor: 'background.default' }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Details:
                        </Typography>
                        <pre style={{ margin: 0, fontSize: '0.875rem' }}>
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </React.Fragment>
            ))}
          </TableBody>
        </Table>

        <TablePagination
          rowsPerPageOptions={[10, 25, 50, 100]}
          component="div"
          count={total}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
        />
      </TableContainer>
    </Box>
  );
};
