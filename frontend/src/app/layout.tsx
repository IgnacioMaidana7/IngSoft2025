import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { NotificationsProvider } from "@/context/NotificationsContext";
import { ToastProvider } from "@/components/feedback/ToastProvider";
import ConditionalNavbar from "@/components/layout/ConditionalNavbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sistema de Gestión - AppProductos",
  description: "Sistema integral para gestión de inventario, productos, ventas y empleados",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="manifest" href="/manifest.webmanifest" />
        <meta name="theme-color" content="#0ea5e9" />
      </head>
      <body className={`${geistSans.className} ${geistMono.className} bg-background text-text antialiased`}>
        <AuthProvider>
          <NotificationsProvider>
            <ConditionalNavbar>
              <ToastProvider>
                {children}
              </ToastProvider>
            </ConditionalNavbar>
          </NotificationsProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
