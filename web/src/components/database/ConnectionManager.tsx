import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Typography,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Cable,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-toastify';
import api from '@services/api';
import type { DatabaseConnection, DatabaseType } from '@types/index';

export const ConnectionManager: React.FC = () => {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingConnection, setEditingConnection] = useState<DatabaseConnection | null>(null);

  const { data: connections, isLoading } = useQuery({
    queryKey: ['connections'],
    queryFn: async () => {
      const response = await api.getConnections();
      return response.data || [];
    },
  });

  const createMutation = useMutation({
    mutationFn: (connection: any) => api.createConnection(connection),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connections'] });
      toast.success('Connection created successfully');
      setDialogOpen(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to create connection');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      api.updateConnection(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connections'] });
      toast.success('Connection updated successfully');
      setDialogOpen(false);
      setEditingConnection(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteConnection(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connections'] });
      toast.success('Connection deleted successfully');
    },
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => api.testConnection(id),
    onSuccess: () => {
      toast.success('Connection test successful');
      queryClient.invalidateQueries({ queryKey: ['connections'] });
    },
    onError: () => {
      toast.error('Connection test failed');
    },
  });

  const handleEdit = (connection: DatabaseConnection) => {
    setEditingConnection(connection);
    setDialogOpen(true);
  };

  const handleCreate = () => {
    setEditingConnection(null);
    setDialogOpen(true);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle color="success" />;
      case 'disconnected':
        return <Cable color="disabled" />;
      case 'error':
        return <Error color="error" />;
      default:
        return <Cable />;
    }
  };

  if (isLoading) {
    return <Typography>Loading connections...</Typography>;
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="h5">Database Connections</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleCreate}
        >
          New Connection
        </Button>
      </Box>

      <Grid container spacing={3}>
        {connections?.map((connection) => (
          <Grid item xs={12} sm={6} md={4} key={connection.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6">{connection.name}</Typography>
                  {getStatusIcon(connection.status)}
                </Box>

                <Typography color="text.secondary" gutterBottom>
                  {connection.type.toUpperCase()}
                </Typography>

                <Typography variant="body2">
                  Host: {connection.host}:{connection.port}
                </Typography>
                <Typography variant="body2">
                  Database: {connection.database}
                </Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  User: {connection.username}
                </Typography>

                {connection.lastUsed && (
                  <Chip
                    label={`Last used: ${new Date(connection.lastUsed).toLocaleDateString()}`}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                )}
              </CardContent>

              <CardActions>
                <Button
                  size="small"
                  onClick={() => testMutation.mutate(connection.id)}
                >
                  Test
                </Button>
                <IconButton
                  size="small"
                  onClick={() => handleEdit(connection)}
                >
                  <Edit />
                </IconButton>
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => deleteMutation.mutate(connection.id)}
                >
                  <Delete />
                </IconButton>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <ConnectionDialog
        open={dialogOpen}
        connection={editingConnection}
        onClose={() => {
          setDialogOpen(false);
          setEditingConnection(null);
        }}
        onSave={(data) => {
          if (editingConnection) {
            updateMutation.mutate({ id: editingConnection.id, data });
          } else {
            createMutation.mutate(data);
          }
        }}
      />
    </Box>
  );
};

interface ConnectionDialogProps {
  open: boolean;
  connection: DatabaseConnection | null;
  onClose: () => void;
  onSave: (data: any) => void;
}

const ConnectionDialog: React.FC<ConnectionDialogProps> = ({
  open,
  connection,
  onClose,
  onSave,
}) => {
  const [formData, setFormData] = useState({
    name: '',
    type: 'postgresql' as DatabaseType,
    host: 'localhost',
    port: 5432,
    database: '',
    username: '',
    password: '',
    ssl: false,
  });

  useEffect(() => {
    if (connection) {
      setFormData({
        name: connection.name,
        type: connection.type,
        host: connection.host,
        port: connection.port,
        database: connection.database,
        username: connection.username,
        password: '',
        ssl: connection.ssl || false,
      });
    }
  }, [connection]);

  const handleSubmit = () => {
    onSave(formData);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {connection ? 'Edit Connection' : 'New Connection'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            fullWidth
            label="Connection Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />

          <TextField
            fullWidth
            select
            label="Database Type"
            value={formData.type}
            onChange={(e) =>
              setFormData({ ...formData, type: e.target.value as DatabaseType })
            }
          >
            <MenuItem value="postgresql">PostgreSQL</MenuItem>
            <MenuItem value="mysql">MySQL</MenuItem>
            <MenuItem value="mongodb">MongoDB</MenuItem>
            <MenuItem value="redis">Redis</MenuItem>
            <MenuItem value="sqlite">SQLite</MenuItem>
          </TextField>

          <TextField
            fullWidth
            label="Host"
            value={formData.host}
            onChange={(e) => setFormData({ ...formData, host: e.target.value })}
            required
          />

          <TextField
            fullWidth
            label="Port"
            type="number"
            value={formData.port}
            onChange={(e) =>
              setFormData({ ...formData, port: parseInt(e.target.value) })
            }
            required
          />

          <TextField
            fullWidth
            label="Database"
            value={formData.database}
            onChange={(e) => setFormData({ ...formData, database: e.target.value })}
            required
          />

          <TextField
            fullWidth
            label="Username"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            required
          />

          <TextField
            fullWidth
            label="Password"
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            placeholder={connection ? '(unchanged)' : ''}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};
