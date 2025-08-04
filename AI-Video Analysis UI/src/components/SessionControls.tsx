import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, Trash2, Settings, Play, Pause } from "lucide-react";
import { toast } from "@/hooks/use-toast";

interface SessionControlsProps {
  sessionId: string;
  isActive: boolean;
  onNewSession: () => void;
  onClearData: () => void;
  onToggleSession: () => void;
}

export const SessionControls = ({ 
  sessionId, 
  isActive, 
  onNewSession, 
  onClearData, 
  onToggleSession 
}: SessionControlsProps) => {
  const handleNewSession = () => {
    onNewSession();
    toast({
      title: "New session started",
      description: "Previous session data has been archived",
    });
  };

  const handleClearData = () => {
    onClearData();
    toast({
      title: "Data cleared",
      description: "All session data has been removed",
      variant: "destructive",
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Session Control
          </span>
          <Badge variant={isActive ? "default" : "secondary"}>
            {isActive ? "Active" : "Paused"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Session ID</label>
          <div className="flex items-center gap-2">
            <code className="flex-1 px-3 py-2 bg-muted rounded-md text-sm font-mono">
              {sessionId}
            </code>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Button
            onClick={onToggleSession}
            variant={isActive ? "outline" : "default"}
            className="flex items-center gap-2"
          >
            {isActive ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {isActive ? "Pause" : "Resume"}
          </Button>

          <Button
            onClick={handleNewSession}
            variant="outline"
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            New Session
          </Button>
        </div>

        <Button
          onClick={handleClearData}
          variant="destructive"
          className="w-full flex items-center gap-2"
        >
          <Trash2 className="h-4 w-4" />
          Clear All Data
        </Button>
      </CardContent>
    </Card>
  );
};