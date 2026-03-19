import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useSSE } from './useSSE';


function createStreamResponse(chunks, options = {}) {
  const encoder = new TextEncoder();
  const body = new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });

  return {
    ok: options.ok ?? true,
    status: options.status ?? 200,
    body,
  };
}


describe('useSSE', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('adds a warning notice when the stream ends without a done event', async () => {
    // 只喂一个片段，模拟流中断但没有收到 done 的场景。
    const dispatch = vi.fn();
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        createStreamResponse([
          'event: system_notice\ndata: {"message":"正在分析"}\r\n\r\n',
        ]),
      ),
    );

    const { result } = renderHook(() => useSSE(dispatch));

    await act(async () => {
      await result.current.startAnalysis('测试问题');
    });

    expect(dispatch).toHaveBeenCalledWith({ type: 'START_THINKING' });
    expect(dispatch).toHaveBeenCalledWith({
      type: 'ADD_USER_MESSAGE',
      payload: '测试问题',
    });
    expect(dispatch).toHaveBeenCalledWith({
      type: 'ADD_SYSTEM_NOTICE',
      payload: { message: '正在分析' },
    });
    expect(dispatch).toHaveBeenCalledWith({
      type: 'ADD_SYSTEM_NOTICE',
      payload: { message: '⚠️ 分析流意外中断，请重试。' },
    });
    expect(dispatch).toHaveBeenCalledWith({ type: 'SET_DONE' });
  });

  it('shows backend analysis errors and completes the session', async () => {
    // 后端主动发 analysis_error 时，前端要展示提示并恢复到可继续提问的状态。
    const dispatch = vi.fn();
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        createStreamResponse([
          'event: analysis_error\ndata: {"code":"model_timeout","message":"模型响应超时，请稍后重试。"}\r\n\r\n',
          'event: done\ndata: {}\r\n\r\n',
        ]),
      ),
    );

    const { result } = renderHook(() => useSSE(dispatch));

    await act(async () => {
      await result.current.startAnalysis('测试问题');
    });

    expect(dispatch).toHaveBeenCalledWith({
      type: 'ADD_SYSTEM_NOTICE',
      payload: { message: '模型响应超时，请稍后重试。' },
    });
    expect(dispatch).toHaveBeenCalledWith({ type: 'SET_DONE' });
  });
});
