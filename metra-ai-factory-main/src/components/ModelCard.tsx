import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useModelStore } from '@/stores/modelStore';
import { Heart, Download } from 'lucide-react';

interface Model {
  modelId: string;
  description: string;
  tags: string[];
  downloads: number;
  likes: number;
}

interface ModelCardProps {
  model: Model;
}

export function ModelCard({ model }: ModelCardProps) {
  const navigate = useNavigate();
  const { setSelectedModelId } = useModelStore();

  const handleSelect = () => {
    setSelectedModelId(model.modelId);
    navigate('/data-builder');
  };

  return (
    <Card className="flex flex-col justify-between">
      <CardHeader>
        <CardTitle className="text-lg">{model.modelId}</CardTitle>
        <CardDescription>{model.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2 mb-4">
          {model.tags.slice(0, 5).map((tag) => (
            <Badge key={tag} variant="secondary">{tag}</Badge>
          ))}
        </div>
        <div className="flex items-center text-sm text-muted-foreground gap-4">
            <div className="flex items-center gap-1">
                <Heart className="w-4 h-4" />
                <span>{model.likes.toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-1">
                <Download className="w-4 h-4" />
                <span>{model.downloads.toLocaleString()}</span>
            </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button onClick={handleSelect} className="w-full">Select and Continue</Button>
      </CardFooter>
    </Card>
  );
} 