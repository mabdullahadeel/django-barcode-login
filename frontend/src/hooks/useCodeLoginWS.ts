import { useEffect, useRef, useState } from "react";
import { useAuth } from "./useAuth";

const socketBasePath = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
interface MessageEvent {
  type: string;
  data: any;
}

export const useCodeLoginWS = () => {
  const socket = useRef<WebSocket | null>(null);
  const listeners = useRef<Map<string, (e: any) => void>>(new Map());
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const { codeLogin } = useAuth();

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);

  const connect = async (wsToken: string) => {
    const url = `${socketBasePath}/ws/code_auth/${wsToken}/`;
    socket.current = new WebSocket(url);
    if (socket.current) {
      disconnect();
    }
    socket.current.onclose = () => {
      listeners.current.clear();
    };
    socket.current.onmessage = (e) => {
      handleSocketMessages(e);
    };
    socket.current.onerror = () => {
      setError("Error connecting to server");
      setLoading(false);
    };
    socket.current.onopen = () => {
      registerListener("token", handleCodeLogin);
      setLoading(false);
    };
  };

  const disconnect = () => {
    socket.current?.close();
  };

  const handleSocketMessages = (e: globalThis.MessageEvent<any>) => {
    const message: MessageEvent = JSON.parse(e.data);
    const listener = listeners.current.get(message.type);
    if (listener) {
      listener(message.data);
    }
  };

  const registerListener = (key: string, cb: (data: any) => void) => {
    listeners.current.set(key, cb);
  };

  const handleCodeLogin = async (token: string) => {
    try {
      setLoading(true);
      await codeLogin(token);
    } catch (error) {
      setError("Error logging in");
      console.log(error);
    } finally {
      setLoading(false);
    }
  };

  return { connect, disconnect, error, loading };
};
