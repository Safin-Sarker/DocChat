import { MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
}

const sizeMap = {
  sm: { icon: 'h-5 w-5', text: 'text-base' },
  md: { icon: 'h-6 w-6', text: 'text-lg' },
  lg: { icon: 'h-8 w-8', text: 'text-xl' },
};

export function Logo({ size = 'md', showText = true, className }: LogoProps) {
  const { icon, text } = sizeMap[size];

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="flex items-center justify-center rounded-lg bg-primary p-1.5">
        <MessageSquare className={cn(icon, 'text-primary-foreground')} />
      </div>
      {showText && (
        <span className={cn('font-semibold text-foreground', text)}>
          DocChat
        </span>
      )}
    </div>
  );
}
