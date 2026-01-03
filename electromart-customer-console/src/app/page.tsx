'use client';

import { Box } from '@mui/material';
import ErrorBoundary from "@/components/ErrorBoundary";
import ChatInterface from "@/components/ChatInterface";


export default function Home() {
  return (
    <ErrorBoundary>
      <Box sx={{ height: '100vh', width: '100vw', overflow: 'hidden' }}>
        <ChatInterface />
      </Box>
    </ErrorBoundary>
  );
}
