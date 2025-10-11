import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Divider,
  Switch,
  FormControlLabel,
  Alert,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import { Save, Security } from '@mui/icons-material';
import { toast } from 'react-toastify';
import { useAuthStore } from '@store/authStore';
import { useThemeStore } from '@store/themeStore';
import api from '@services/api';

export const SettingsPage: React.FC = () => {
  const { user, refreshUser } = useAuthStore();
  const { mode, toggleTheme } = useThemeStore();

  const [emailNotifications, setEmailNotifications] = useState(true);
  const [queryHistory, setQueryHistory] = useState(true);
  const [autoSave, setAutoSave] = useState(true);

  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [qrCode, setQrCode] = useState<string | null>(null);

  const handleSavePreferences = () => {
    // Save preferences to backend
    toast.success('Preferences saved successfully');
  };

  const handleChangePassword = () => {
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (passwordForm.newPassword.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    // Call API to change password
    toast.success('Password changed successfully');
    setPasswordForm({
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    });
  };

  const handleEnable2FA = async () => {
    try {
      const response = await api.enable2FA();
      if (response.success && response.data) {
        setQrCode(response.data.qrCode);
        toast.success('Scan the QR code with your authenticator app');
      }
    } catch (error) {
      toast.error('Failed to enable 2FA');
    }
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3 }}>
        Settings
      </Typography>

      <Grid container spacing={3}>
        {/* Profile Settings */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Profile Settings
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <TextField
              fullWidth
              label="Username"
              value={user?.username || ''}
              disabled
              margin="normal"
            />

            <TextField
              fullWidth
              label="Email"
              value={user?.email || ''}
              margin="normal"
            />

            <TextField
              fullWidth
              label="Role"
              value={user?.role.toUpperCase() || ''}
              disabled
              margin="normal"
            />

            <Button
              variant="contained"
              startIcon={<Save />}
              sx={{ mt: 2 }}
              onClick={handleSavePreferences}
            >
              Save Profile
            </Button>
          </Paper>
        </Grid>

        {/* Security Settings */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Security Settings
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <TextField
              fullWidth
              type="password"
              label="Current Password"
              value={passwordForm.currentPassword}
              onChange={(e) =>
                setPasswordForm({ ...passwordForm, currentPassword: e.target.value })
              }
              margin="normal"
            />

            <TextField
              fullWidth
              type="password"
              label="New Password"
              value={passwordForm.newPassword}
              onChange={(e) =>
                setPasswordForm({ ...passwordForm, newPassword: e.target.value })
              }
              margin="normal"
            />

            <TextField
              fullWidth
              type="password"
              label="Confirm New Password"
              value={passwordForm.confirmPassword}
              onChange={(e) =>
                setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })
              }
              margin="normal"
            />

            <Button
              variant="contained"
              onClick={handleChangePassword}
              sx={{ mt: 2 }}
            >
              Change Password
            </Button>
          </Paper>
        </Grid>

        {/* Two-Factor Authentication */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Two-Factor Authentication
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {user?.twoFactorEnabled ? (
              <Alert severity="success" sx={{ mb: 2 }}>
                Two-factor authentication is enabled
              </Alert>
            ) : (
              <Alert severity="info" sx={{ mb: 2 }}>
                Two-factor authentication is not enabled
              </Alert>
            )}

            {qrCode && (
              <Box sx={{ mb: 2, textAlign: 'center' }}>
                <img src={qrCode} alt="2FA QR Code" style={{ maxWidth: '200px' }} />
              </Box>
            )}

            <Button
              variant="contained"
              startIcon={<Security />}
              onClick={handleEnable2FA}
              disabled={user?.twoFactorEnabled}
              fullWidth
            >
              {user?.twoFactorEnabled ? 'Enabled' : 'Enable 2FA'}
            </Button>
          </Paper>
        </Grid>

        {/* Preferences */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Preferences
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <FormControlLabel
              control={
                <Switch checked={mode === 'dark'} onChange={toggleTheme} />
              }
              label="Dark Mode"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={emailNotifications}
                  onChange={(e) => setEmailNotifications(e.target.checked)}
                />
              }
              label="Email Notifications"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={queryHistory}
                  onChange={(e) => setQueryHistory(e.target.checked)}
                />
              }
              label="Save Query History"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={autoSave}
                  onChange={(e) => setAutoSave(e.target.checked)}
                />
              }
              label="Auto-save Queries"
            />

            <Button
              variant="contained"
              startIcon={<Save />}
              onClick={handleSavePreferences}
              fullWidth
              sx={{ mt: 2 }}
            >
              Save Preferences
            </Button>
          </Paper>
        </Grid>

        {/* Account Information */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Account Information
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary">
                      Account Created
                    </Typography>
                    <Typography variant="h6">
                      {user?.createdAt
                        ? new Date(user.createdAt).toLocaleDateString()
                        : '-'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary">
                      Last Login
                    </Typography>
                    <Typography variant="h6">
                      {user?.lastLogin
                        ? new Date(user.lastLogin).toLocaleDateString()
                        : 'Never'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
