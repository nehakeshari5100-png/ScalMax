'use client';

import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface Column<T> {
  key: string;
  header: string;
  render: (item: T) => React.ReactNode;
  className?: string;
  sortable?: boolean;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (item: T) => void;
  className?: string;
  emptyMessage?: string;
}

export function Table<T extends { id: string }>({ columns, data, onRowClick, className, emptyMessage = 'No data' }: TableProps<T>) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-[var(--color-text-muted)] text-sm">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className={cn('overflow-x-auto scrollbar-hide', className)}>
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/5">
            {columns.map(col => (
              <th
                key={col.key}
                className={cn(
                  'text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider px-4 py-3',
                  col.className
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item, index) => (
            <motion.tr
              key={item.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.03, duration: 0.3 }}
              className={cn(
                'border-b border-white/5 transition-colors duration-150',
                onRowClick && 'cursor-pointer hover:bg-white/[0.02]'
              )}
              onClick={() => onRowClick?.(item)}
            >
              {columns.map(col => (
                <td key={col.key} className={cn('px-4 py-3 text-sm', col.className)}>
                  {col.render(item)}
                </td>
              ))}
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
