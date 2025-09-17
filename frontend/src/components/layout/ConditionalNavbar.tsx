'use client';

import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';
import Navbar from '@/components/navigation/Navbar';

interface ConditionalNavbarProps {
  children: ReactNode;
}

export default function ConditionalNavbar({ children }: ConditionalNavbarProps) {
  const pathname = usePathname();
  
  // Páginas que NO deben mostrar el navbar
  const authPages = ['/login', '/register'];
  const shouldShowNavbar = !authPages.some(page => pathname?.startsWith(page));

  return (
    <>
      {shouldShowNavbar && <Navbar />}
      {children}
    </>
  );
}