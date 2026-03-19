import { useCallback, useRef } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export const useSSE = (dispatch) => {
  const abortControllerRef = useRef(null);

  const startAnalysis = useCallback(async (question) => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    dispatch({ type: 'START_THINKING' });
    dispatch({ type: 'ADD_USER_MESSAGE', payload: question });
    
    try {
      // 这里需要用 POST 传递问题，原生 EventSource 不支持 POST + body。
      // 所以改用 fetch 读取流式响应，再手动解析 SSE。
      const response = await fetch(`${API_BASE_URL}/api/think`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ question }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Empty SSE response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let receivedDone = false;
      
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // SSE 事件之间用空行分隔，这里按双换行切分
        const chunks = buffer.split('\r\n\r\n');
        // 最后一个分片可能还没收完整，保留到下一轮继续拼接
        buffer = chunks.pop() || '';
        
        for (const chunk of chunks) {
          if (!chunk.trim()) continue;
          
          const lines = chunk.split('\n');
          let eventName = 'message';
          let dataStr = '';
          
          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventName = line.replace('event:', '').trim();
            } else if (line.startsWith('data:')) {
              dataStr = line.replace('data:', '').trim();
            }
          }

          if (!dataStr) continue;

          let data = {};
          try {
            data = JSON.parse(dataStr);
          } catch {
             data = dataStr;
          }

          // 按事件类型分发到对应的状态更新
          switch (eventName) {
            case 'system_notice':
              dispatch({ type: 'ADD_SYSTEM_NOTICE', payload: data });
              break;
            case 'expert_join':
              dispatch({ type: 'ADD_EXPERT', payload: data });
              break;
            case 'expert_typing':
              dispatch({ type: 'SET_TYPING', payload: data });
              break;
            case 'expert_message':
              dispatch({ type: 'ADD_EXPERT_MESSAGE', payload: data });
              break;
            case 'summary_message':
              dispatch({ type: 'ADD_SUMMARY', payload: data });
              break;
            case 'analysis_error':
              // 后端显式返回的业务错误，直接转成提示并结束本轮分析。
              dispatch({ type: 'ADD_SYSTEM_NOTICE', payload: { message: data.message } });
              dispatch({ type: 'SET_DONE' });
              break;
            case 'done':
              receivedDone = true;
              dispatch({ type: 'SET_DONE' });
              break;
            default:
              console.log('Unknown event:', eventName);
          }
        }
      }

      if (!receivedDone) {
        // 网络还没报错，但流已经结束，说明响应在中途断了。
        dispatch({
          type: 'ADD_SYSTEM_NOTICE',
          payload: { message: '⚠️ 分析流意外中断，请重试。' },
        });
        dispatch({ type: 'SET_DONE' });
      }
      
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }

      console.error("SSE Error:", err);
      // 网络级失败统一兜底，保证输入框和状态机可以恢复。
      dispatch({ type: 'ADD_SYSTEM_NOTICE', payload: { message: '❌ 连接服务器失败或出现错误' } });
      dispatch({ type: 'SET_DONE' });
    } finally {
      abortControllerRef.current = null;
    }

  }, [dispatch]);

  const stopAnalysis = useCallback(() => {
    // 取消时先中断请求，再清理前端状态。
    abortControllerRef.current?.abort();
    dispatch({ type: 'SET_DONE' });
  }, [dispatch]);

  return { startAnalysis, stopAnalysis };
};
