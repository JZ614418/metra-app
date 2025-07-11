import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'default' | 'outline' | 'secondary';
  };
  badge?: {
    text: string;
    variant?: 'default' | 'secondary' | 'outline';
  };
  children?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  action,
  badge,
  children
}) => {
  return (
    <Card className="border-dashed border-2 border-gray-200 bg-gray-50/30">
      <CardContent className="flex flex-col items-center justify-center p-12 text-center">
        <div className="rounded-full bg-gray-100 p-6 mb-4">
          <Icon className="h-8 w-8 text-gray-400" />
        </div>
        
        <div className="space-y-2 mb-6">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600 max-w-md">{description}</p>
        </div>

        {badge && (
          <Badge variant={badge.variant || 'secondary'} className="mb-4">
            {badge.text}
          </Badge>
        )}

        {action && (
          <Button 
            onClick={action.onClick}
            variant={action.variant || 'default'}
            className="bg-gray-900 hover:bg-gray-800"
          >
            {action.label}
          </Button>
        )}

        {children && (
          <div className="mt-6 w-full">
            {children}
          </div>
        )}
      </CardContent>
    </Card>
  );
};