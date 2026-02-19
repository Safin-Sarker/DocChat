import { PanelLeft } from 'lucide-react';
import { Button } from '@/presentation/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/presentation/ui/tooltip';
import { Logo } from '@/presentation/shared/Logo';
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
    <header className="h-14 border-b border-border/40 bg-background/95 backdrop-blur-safe sticky top-0 z-50 flex items-center justify-between px-4 shadow-[0_1px_3px_0_rgb(0_0_0/0.02)]">
      <div className="flex items-center gap-3">
        {/* Only show open-sidebar button when sidebar is hidden */}
        {!isSidebarOpen && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-lg hover:bg-muted"
                onClick={onToggleSidebar}
                aria-label="Open sidebar"
              >
                <PanelLeft className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">Open sidebar</TooltipContent>
          </Tooltip>
        )}
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
              <div
                className={cn(
                  'h-2 w-2 rounded-full',
                  isConnected
                    ? 'bg-green-500 shadow-[0_0_6px_1px_rgb(34_197_94/0.4)]'
                    : 'bg-destructive animate-pulse'
                )}
              />
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
