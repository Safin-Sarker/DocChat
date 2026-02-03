import { PanelLeftClose, PanelLeft, Wifi, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Logo } from '@/components/shared/Logo';
import { cn } from '@/lib/utils';

interface HeaderProps {
  isConnected: boolean;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
}

export function Header({
  isConnected,
  isSidebarOpen,
  onToggleSidebar,
}: HeaderProps) {
  return (
    <header className="h-14 border-b bg-background/95 backdrop-blur-safe sticky top-0 z-50 flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 lg:hidden"
          onClick={onToggleSidebar}
          aria-label={isSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          {isSidebarOpen ? (
            <PanelLeftClose className="h-5 w-5" />
          ) : (
            <PanelLeft className="h-5 w-5" />
          )}
        </Button>
        <Logo size="md" />
      </div>

      <div className="flex items-center gap-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <div
              className={cn(
                'flex items-center gap-1.5 px-2 py-1 rounded-full text-xs',
                isConnected
                  ? 'bg-green-500/10 text-green-600 dark:text-green-400'
                  : 'bg-destructive/10 text-destructive'
              )}
            >
              {isConnected ? (
                <Wifi className="h-3 w-3" />
              ) : (
                <WifiOff className="h-3 w-3" />
              )}
              <span className="hidden sm:inline">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            {isConnected ? 'Server connected' : 'Server disconnected'}
          </TooltipContent>
        </Tooltip>
      </div>
    </header>
  );
}
