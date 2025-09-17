'use client';

import { ReactNode } from 'react';
import Navbar from '@/components/navigation/Navbar';

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <>
      <Navbar />
      {children}
    </>
  );
}