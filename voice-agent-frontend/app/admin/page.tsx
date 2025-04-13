"use client";

import axios from "axios";
import { format } from "date-fns";
import { ja } from "date-fns/locale";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import { FiArrowLeft } from "react-icons/fi";

// 会話データの型定義
interface Conversation {
  id: string;
  timestamp: string;
  action_types: string[];
  order_id: string | null;
  user_id: string | null;
}

interface ConversationDetail extends Conversation {
  conversation_history: {
    role: string;
    content: string;
    timestamp: string;
  }[];
  executed_functions: {
    function: string;
    arguments: Record<string, any>;
    timestamp: string;
  }[];
}

export default function AdminPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConversation, setSelectedConversation] = useState<ConversationDetail | null>(null);

  // 会話一覧を取得
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        setLoading(true);
        const response = await axios.get("http://localhost:5001/api/conversations");
        setConversations(response.data);
        setError(null);
      } catch (err) {
        console.error("会話の取得に失敗しました:", err);
        setError("会話の取得に失敗しました。サーバーが起動しているか確認してください。");
      } finally {
        setLoading(false);
      }
    };

    fetchConversations();
  }, []);

  // 会話詳細を取得
  const fetchConversationDetail = async (id: string) => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:5001/api/conversations/${id}`);
      setSelectedConversation(response.data);
      setError(null);
    } catch (err) {
      console.error("会話詳細の取得に失敗しました:", err);
      setError("会話詳細の取得に失敗しました。");
    } finally {
      setLoading(false);
    }
  };

  // 日時をフォーマット
  const formatDate = (dateString: string) => {
    if (!dateString) return "-";
    return format(new Date(dateString), "yyyy年MM月dd日 HH:mm:ss", { locale: ja });
  };

  // 会話詳細を閉じる
  const closeDetail = () => {
    setSelectedConversation(null);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        <header className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">楽々ECコールセンター 管理画面</h1>
          <Link href="/" className="flex items-center text-blue-600 hover:text-blue-800">
            <FiArrowLeft className="mr-1" />
            通話画面に戻る
          </Link>
        </header>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {loading && !selectedConversation && (
          <div className="text-center py-10">
            <p className="text-gray-600">読み込み中...</p>
          </div>
        )}

        {!loading && conversations.length === 0 && !selectedConversation && (
          <div className="text-center py-10 bg-white rounded-lg shadow">
            <p className="text-gray-600">会話履歴がありません</p>
          </div>
        )}

        {!selectedConversation ? (
          // 会話一覧表示
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    日時
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    問い合わせ分類
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    注文ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ユーザーID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {conversations.map((conversation) => (
                  <tr key={conversation.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(conversation.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex flex-wrap gap-1">
                        {conversation.action_types.map((action, index) => (
                          <span
                            key={index}
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              action === "確認"
                                ? "bg-blue-100 text-blue-800"
                                : action === "変更"
                                  ? "bg-yellow-100 text-yellow-800"
                                  : action === "キャンセル"
                                    ? "bg-red-100 text-red-800"
                                    : "bg-gray-100 text-gray-800"
                            }`}
                          >
                            {action}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {conversation.order_id || "-"}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {conversation.user_id || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => fetchConversationDetail(conversation.id)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        詳細を見る
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          // 会話詳細表示
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-800">会話詳細</h2>
              <button onClick={closeDetail} className="text-gray-600 hover:text-gray-900">
                ← 一覧に戻る
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">基本情報</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="mb-1">
                    <span className="font-medium">記録時間:</span>{" "}
                    {formatDate(selectedConversation.timestamp)}
                  </p>
                  <p>
                    <span className="font-medium">問い合わせ分類:</span>{" "}
                    <span className="flex flex-wrap gap-1 mt-1">
                      {selectedConversation.action_types.map((action, index) => (
                        <span
                          key={index}
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            action === "確認"
                              ? "bg-blue-100 text-blue-800"
                              : action === "変更"
                                ? "bg-yellow-100 text-yellow-800"
                                : action === "キャンセル"
                                  ? "bg-red-100 text-red-800"
                                  : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {action}
                        </span>
                      ))}
                    </span>
                  </p>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">注文情報</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="mb-1">
                    <span className="font-medium">注文ID:</span>{" "}
                    {selectedConversation.order_id || "-"}
                  </p>
                  <p className="mb-1">
                    <span className="font-medium">ユーザーID:</span>{" "}
                    {selectedConversation.user_id || "-"}
                  </p>
                </div>
              </div>
            </div>

            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-700 mb-2">会話履歴</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                {selectedConversation.conversation_history.map((message, index) => (
                  <div
                    key={index}
                    className={`mb-4 ${message.role === "user" ? "text-right" : "text-left"}`}
                  >
                    <div
                      className={`inline-block max-w-md rounded-lg px-4 py-2 ${
                        message.role === "user"
                          ? "bg-blue-500 text-white"
                          : "bg-gray-200 text-gray-800"
                      }`}
                    >
                      <p>{message.content}</p>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {message.timestamp ? formatDate(message.timestamp) : ""}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {selectedConversation.executed_functions.length > 0 && (
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">実行されたアクション</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  {selectedConversation.executed_functions.map((func, index) => (
                    <div key={index} className="mb-4 pb-4 border-b border-gray-200 last:border-0">
                      <p className="font-medium">
                        {func.function === "check_order_details"
                          ? "注文詳細確認"
                          : func.function === "cancel_order"
                            ? "注文キャンセル"
                            : func.function === "update_order_quantity"
                              ? "注文変更"
                              : func.function}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">{formatDate(func.timestamp)}</p>
                      <div className="mt-2 text-sm">
                        <pre className="bg-gray-100 p-2 rounded overflow-x-auto">
                          {JSON.stringify(func.arguments, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
