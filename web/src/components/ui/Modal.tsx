import type { ReactNode } from 'react';
import { cn } from '../../utils/cn';

interface ModalProps {
  title?: string;
  description?: string | ReactNode;
  isOpen: boolean;
  onClose: () => void;
  children?: ReactNode;
  footer?: ReactNode;
}

export default function Modal({ title, description, isOpen, onClose, children, footer }: ModalProps) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} aria-hidden="true" />
      <div role="dialog" aria-modal="true" className="relative z-10 w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-gray-900">
        {title && <h2 className="mb-1 text-lg font-semibold">{title}</h2>}
        {description && <div className="mb-4 text-sm opacity-80">{description}</div>}
        {children}
        {footer && <div className="mt-5 flex items-center justify-end gap-2">{footer}</div>}
      </div>
    </div>
  );
}
