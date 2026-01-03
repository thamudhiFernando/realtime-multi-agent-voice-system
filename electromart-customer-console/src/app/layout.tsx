import type { Metadata } from 'next';
import ThemeRegistry from './ThemeRegistry';
import './globals.css';
import React from "react";

export const metadata: Metadata = {
  title: 'ElectroMart - Multi-Agent Support System',
  description: 'Intelligent customer support powered by AI agents',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <ThemeRegistry>{children}</ThemeRegistry>
      </body>
    </html>
  );
}
