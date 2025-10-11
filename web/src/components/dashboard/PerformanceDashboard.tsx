import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp,
  Speed,
  Storage,
  QueryStats,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import websocket from '@services/websocket';
import { MessageType } from '@types/index';
import api from '@services/api';

export const PerformanceDashboard: React.FC = () => {
  const [realtimeMetrics, setRealtimeMetrics] = useState<any[]>([]);

  const { data: connections } = useQuery({
    queryKey: ['connections'],
    queryFn: async () => {
      const response = await api.getConnections();
      return response.data || [];
    },
  });

  useEffect(() => {
    // Subscribe to real-time metric updates
    const unsubscribe = websocket.subscribe(
      MessageType.METRIC_UPDATE,
      (payload) => {
        setRealtimeMetrics((prev) => [...prev.slice(-20), payload]);
      }
    );

    return () => unsubscribe();
  }, []);

  // Mock data for demonstration
  const queryPerformanceData = [
    { time: '00:00', queries: 45, avgTime: 120 },
    { time: '04:00', queries: 32, avgTime: 95 },
    { time: '08:00', queries: 78, avgTime: 150 },
    { time: '12:00', queries: 125, avgTime: 180 },
    { time: '16:00', queries: 95, avgTime: 140 },
    { time: '20:00', queries: 67, avgTime: 110 },
  ];

  const connectionStatusData = [
    { name: 'Active', value: connections?.filter((c: any) => c.status === 'connected').length || 0 },
    { name: 'Inactive', value: connections?.filter((c: any) => c.status === 'disconnected').length || 0 },
    { name: 'Error', value: connections?.filter((c: any) => c.status === 'error').length || 0 },
  ];

  const cpuUsageData = [
    { time: '5m', usage: 45 },
    { time: '4m', usage: 52 },
    { time: '3m', usage: 48 },
    { time: '2m', usage: 65 },
    { time: '1m', usage: 58 },
    { time: 'now', usage: 55 },
  ];

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Performance Dashboard
      </Typography>

      {/* Metric Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <QueryStats color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Total Queries</Typography>
              </Box>
              <Typography variant="h4">1,247</Typography>
              <Typography variant="body2" color="text.secondary">
                +12% from last hour
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Speed color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Avg Response</Typography>
              </Box>
              <Typography variant="h4">142ms</Typography>
              <Typography variant="body2" color="text.secondary">
                -8% from yesterday
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Storage color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6">Connections</Typography>
              </Box>
              <Typography variant="h4">{connections?.length || 0}</Typography>
              <Typography variant="body2" color="text.secondary">
                {connectionStatusData[0].value} active
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUp color="error" sx={{ mr: 1 }} />
                <Typography variant="h6">Error Rate</Typography>
              </Box>
              <Typography variant="h4">0.8%</Typography>
              <Typography variant="body2" color="text.secondary">
                +0.2% from last hour
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Query Performance */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Query Performance
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={queryPerformanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="queries"
                  stroke="#8884d8"
                  fill="#8884d8"
                  name="Query Count"
                />
                <Area
                  yAxisId="right"
                  type="monotone"
                  dataKey="avgTime"
                  stroke="#82ca9d"
                  fill="#82ca9d"
                  name="Avg Time (ms)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* CPU Usage */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              CPU Usage
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={cpuUsageData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="usage"
                  stroke="#ff7c7c"
                  strokeWidth={2}
                  name="CPU %"
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Connection Status */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Connection Status
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={connectionStatusData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* System Health */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              System Health
            </Typography>

            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Memory Usage</Typography>
                <Typography variant="body2">2.4 GB / 8 GB</Typography>
              </Box>
              <LinearProgress variant="determinate" value={30} sx={{ mb: 2 }} />

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Disk Usage</Typography>
                <Typography variant="body2">45 GB / 100 GB</Typography>
              </Box>
              <LinearProgress variant="determinate" value={45} color="warning" sx={{ mb: 2 }} />

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Network I/O</Typography>
                <Typography variant="body2">125 MB/s</Typography>
              </Box>
              <LinearProgress variant="determinate" value={65} color="success" sx={{ mb: 2 }} />

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Cache Hit Rate</Typography>
                <Typography variant="body2">87%</Typography>
              </Box>
              <LinearProgress variant="determinate" value={87} color="success" />
            </Box>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <Box sx={{ maxHeight: 200, overflowY: 'auto' }}>
              {[...Array(10)].map((_, i) => (
                <Box
                  key={i}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    py: 1,
                    borderBottom: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="body2">
                    Query executed on connection "Production DB"
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {i + 1} min ago
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
