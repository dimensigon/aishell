import React, { useState, useRef } from 'react';
import {
  Box,
  Button,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Typography,
  Tabs,
  Tab,
  CircularProgress,
} from '@mui/material';
import { PlayArrow, Save, History } from '@mui/icons-material';
import Editor from '@monaco-editor/react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { toast } from 'react-toastify';
import api from '@services/api';
import { QueryResultsViewer } from './QueryResultsViewer';
import type { DatabaseConnection, QueryResult } from '@types/index';

export const QueryEditor: React.FC = () => {
  const [selectedConnection, setSelectedConnection] = useState<string>('');
  const [query, setQuery] = useState<string>('-- Write your SQL query here\nSELECT * FROM users LIMIT 10;');
  const [tabValue, setTabValue] = useState(0);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const editorRef = useRef<any>(null);

  const { data: connections } = useQuery({
    queryKey: ['connections'],
    queryFn: async () => {
      const response = await api.getConnections();
      return response.data || [];
    },
  });

  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!selectedConnection) {
        throw new Error('Please select a connection');
      }
      if (!query.trim()) {
        throw new Error('Please enter a query');
      }

      const response = await api.executeQuery({
        connectionId: selectedConnection,
        query: query.trim(),
      });

      return response.data;
    },
    onSuccess: (data) => {
      if (data) {
        setQueryResult(data);
        setTabValue(1);
        toast.success(`Query executed successfully (${data.rowCount} rows, ${data.executionTime}ms)`);
      }
    },
    onError: (error: any) => {
      toast.error(error.message || 'Query execution failed');
    },
  });

  const handleExecute = () => {
    executeMutation.mutate();
  };

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
  };

  const handleSaveQuery = () => {
    // Save to localStorage or backend
    const saved = localStorage.getItem('savedQueries') || '[]';
    const queries = JSON.parse(saved);
    queries.push({
      query,
      connectionId: selectedConnection,
      timestamp: new Date().toISOString(),
    });
    localStorage.setItem('savedQueries', JSON.stringify(queries));
    toast.success('Query saved');
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Toolbar */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl sx={{ minWidth: 250 }}>
            <InputLabel>Connection</InputLabel>
            <Select
              value={selectedConnection}
              label="Connection"
              onChange={(e) => setSelectedConnection(e.target.value)}
            >
              {connections?.map((conn: DatabaseConnection) => (
                <MenuItem key={conn.id} value={conn.id}>
                  {conn.name} ({conn.type})
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="contained"
            startIcon={executeMutation.isPending ? <CircularProgress size={20} /> : <PlayArrow />}
            onClick={handleExecute}
            disabled={executeMutation.isPending || !selectedConnection}
          >
            Execute
          </Button>

          <Button
            variant="outlined"
            startIcon={<Save />}
            onClick={handleSaveQuery}
            disabled={!query.trim()}
          >
            Save
          </Button>

          <Button
            variant="outlined"
            startIcon={<History />}
            onClick={() => setTabValue(2)}
          >
            History
          </Button>
        </Box>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label="Query Editor" />
          <Tab label="Results" disabled={!queryResult} />
          <Tab label="History" />
        </Tabs>

        {/* Tab Panels */}
        <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
          {tabValue === 0 && (
            <Editor
              height="100%"
              defaultLanguage="sql"
              value={query}
              onChange={(value) => setQuery(value || '')}
              onMount={handleEditorDidMount}
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                wordWrap: 'on',
                automaticLayout: true,
              }}
            />
          )}

          {tabValue === 1 && queryResult && (
            <QueryResultsViewer result={queryResult} />
          )}

          {tabValue === 2 && (
            <QueryHistory
              connectionId={selectedConnection}
              onSelectQuery={(q) => {
                setQuery(q.query);
                setTabValue(0);
              }}
            />
          )}
        </Box>
      </Paper>
    </Box>
  );
};

interface QueryHistoryProps {
  connectionId: string;
  onSelectQuery: (query: QueryResult) => void;
}

const QueryHistory: React.FC<QueryHistoryProps> = ({ connectionId, onSelectQuery }) => {
  const { data: history, isLoading } = useQuery({
    queryKey: ['queryHistory', connectionId],
    queryFn: async () => {
      const response = await api.getQueryHistory(connectionId || undefined);
      return response.data?.items || [];
    },
    enabled: !!connectionId,
  });

  if (isLoading) {
    return <Box sx={{ p: 2 }}><CircularProgress /></Box>;
  }

  if (!history || history.length === 0) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography>No query history</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2, overflowY: 'auto', height: '100%' }}>
      {history.map((item: QueryResult) => (
        <Paper
          key={item.id}
          sx={{ p: 2, mb: 2, cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
          onClick={() => onSelectQuery(item)}
        >
          <Typography variant="body2" sx={{ fontFamily: 'monospace', mb: 1 }}>
            {item.query}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {new Date(item.timestamp).toLocaleString()} • {item.rowCount} rows • {item.executionTime}ms
          </Typography>
        </Paper>
      ))}
    </Box>
  );
};
