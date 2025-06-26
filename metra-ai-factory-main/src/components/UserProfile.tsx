import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  User, 
  Mail, 
  Phone, 
  CreditCard, 
  Zap, 
  Database, 
  Calendar,
  Settings,
  Shield,
  Bell,
  Key,
  Download,
  BarChart3,
  Check,
  Receipt,
  Loader2
} from 'lucide-react';
import { Label } from '@/components/ui/label';
import { TableHead } from '@/components/ui/table';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { useAuthStore } from '@/stores/authStore';
import { api } from '@/lib/api';
import { useToast } from '@/components/ui/use-toast';

interface UsageStats {
  models_created_this_month: number;
  api_calls_this_month: number;
  training_minutes_this_month: number;
  models_remaining: number;
  api_calls_remaining: number;
  training_minutes_remaining: number;
}

const UserProfile = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(true);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [updating, setUpdating] = useState(false);
  const { user, setUser } = useAuthStore();
  const { toast } = useToast();

  // Form states
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  useEffect(() => {
    loadUsageStats();
  }, []);

  useEffect(() => {
    setFullName(user?.full_name || '');
    setEmail(user?.email || '');
  }, [user]);

  const loadUsageStats = async () => {
    try {
      const stats = await api.getUsageStats();
      setUsage(stats);
    } catch (error) {
      toast({
        title: 'Error loading usage stats',
        description: error instanceof Error ? error.message : 'Something went wrong',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProfile = async () => {
    setUpdating(true);
    try {
      const updatedUser = await api.updateMe({
        email,
        full_name: fullName,
      });
      setUser(updatedUser);
      toast({
        title: 'Profile updated',
        description: 'Your profile has been successfully updated.',
      });
    } catch (error) {
      toast({
        title: 'Update failed',
        description: error instanceof Error ? error.message : 'Something went wrong',
        variant: 'destructive',
      });
    } finally {
      setUpdating(false);
    }
  };

  const handleUpdatePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast({
        title: 'Passwords do not match',
        description: 'Please make sure your passwords match.',
        variant: 'destructive',
      });
      return;
    }

    setUpdating(true);
    try {
      await api.updateMe({
        password: newPassword,
      });
      toast({
        title: 'Password updated',
        description: 'Your password has been successfully updated.',
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      toast({
        title: 'Update failed',
        description: error instanceof Error ? error.message : 'Something went wrong',
        variant: 'destructive',
      });
    } finally {
      setUpdating(false);
    }
  };

  const navItems = [
    { id: 'profile', name: 'Basic Information', icon: User },
    { id: 'usage', name: 'Usage Statistics', icon: BarChart3 },
    { id: 'security', name: 'Security Settings', icon: Shield },
  ];

  const renderProfileTab = () => (
    <div className="space-y-6">
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg">Personal Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <Avatar className="h-20 w-20">
              <AvatarFallback>
                {user?.full_name ? user.full_name.split(' ').map(n => n[0]).join('') : user?.email?.[0].toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <h3 className="text-xl font-semibold">{user?.full_name || 'User'}</h3>
              <p className="text-sm text-gray-600">Free Tier User</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Full Name</Label>
              <Input 
                id="name"
                value={fullName} 
                onChange={(e) => setFullName(e.target.value)}
                disabled={updating}
              />
            </div>
            <div>
              <Label htmlFor="email">Email Address</Label>
              <Input 
                id="email"
                value={email} 
                onChange={(e) => setEmail(e.target.value)}
                disabled={updating}
              />
            </div>
            <div>
              <Label htmlFor="joinDate">Join Date</Label>
              <Input 
                id="joinDate"
                value={user?.created_at ? new Date(user.created_at).toLocaleDateString() : ''} 
                disabled 
              />
            </div>
            <div>
              <Label htmlFor="status">Account Status</Label>
              <div className="mt-2">
                <Badge className={`${user?.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  {user?.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </div>
          </div>
          
          <div className="flex justify-end">
            <Button onClick={handleUpdateProfile} disabled={updating}>
              {updating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Updating...
                </>
              ) : (
                'Save Changes'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderUsageTab = () => (
    <div className="space-y-6">
      {loading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="border-0 shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Models Created</span>
                  <Database className="h-4 w-4 text-gray-400" />
                </div>
                <div className="text-2xl font-bold">
                  {usage?.models_created_this_month || 0} / 3
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {usage?.models_remaining || 0} remaining this month
                </p>
              </CardContent>
            </Card>
            
            <Card className="border-0 shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">API Calls</span>
                  <Zap className="h-4 w-4 text-gray-400" />
                </div>
                <div className="text-2xl font-bold">
                  {usage?.api_calls_this_month || 0} / 1,000
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {usage?.api_calls_remaining || 0} remaining this month
                </p>
              </CardContent>
            </Card>
            
            <Card className="border-0 shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Training Minutes</span>
                  <Calendar className="h-4 w-4 text-gray-400" />
                </div>
                <div className="text-2xl font-bold">
                  {usage?.training_minutes_this_month || 0} / 120
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {usage?.training_minutes_remaining || 0} minutes remaining
                </p>
              </CardContent>
            </Card>
          </div>

          <Card className="border-0 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Current Plan</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Free Plan</h3>
                  <p className="text-sm text-gray-600">Limited features for personal use</p>
                </div>
                <Badge className="bg-blue-100 text-blue-800">Active</Badge>
              </div>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>3 models per month</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>1,000 API calls per month</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>120 training minutes per month</span>
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Basic support</span>
                </div>
              </div>
              <div className="mt-4">
                <Button variant="outline" size="sm">Upgrade Plan</Button>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );

  const renderSecurityTab = () => (
    <div className="space-y-6">
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg">Password Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="currentPassword">Current Password</Label>
            <Input 
              id="currentPassword"
              type="password" 
              placeholder="Enter current password" 
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              disabled={updating}
            />
          </div>
          <div>
            <Label htmlFor="newPassword">New Password</Label>
            <Input 
              id="newPassword"
              type="password" 
              placeholder="Enter new password" 
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              disabled={updating}
            />
          </div>
          <div>
            <Label htmlFor="confirmPassword">Confirm New Password</Label>
            <Input 
              id="confirmPassword"
              type="password" 
              placeholder="Re-enter new password" 
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={updating}
            />
          </div>
          <Button onClick={handleUpdatePassword} disabled={updating || !newPassword}>
            {updating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Updating...
              </>
            ) : (
              'Update Password'
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return renderProfileTab();
      case 'usage':
        return renderUsageTab();
      case 'security':
        return renderSecurityTab();
      default:
        return renderProfileTab();
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Sidebar */}
      <div className="lg:col-span-1">
        <Card className="border-0 shadow-sm">
          <CardContent className="p-0">
            <nav className="space-y-1">
              {navItems.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 text-left text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'bg-gray-100 text-gray-900 border-r-2 border-gray-900'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <tab.icon className="h-4 w-4" />
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </CardContent>
        </Card>
      </div>

      {/* Content */}
      <div className="lg:col-span-3">
        {renderContent()}
      </div>
    </div>
  );
};

export default UserProfile;
