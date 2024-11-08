"use client";
 
import type { ReactNode } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  SimpleTextAttachmentAdapter,
  type ChatModelAdapter,
} from "@assistant-ui/react";


const SERVER_DOMAIN = process.env.NEXT_PUBLIC_SERVER_DOMAIN;
 
const MyModelAdapter: ChatModelAdapter = {
  
  async run({ messages, abortSignal }) {
    let result;
    if (messages.length === 0) {
      result = await fetch(`http://${SERVER_DOMAIN}/chat`, {
        method: "POST",
        signal: abortSignal,
      });
    } else if (messages[messages.length - 1].attachments && messages[messages.length - 1].attachments.length !== 0) {
      console.log('uploading file');
      const formData = new FormData();
      formData.append('file', messages[messages.length - 1].attachments[0].file);
      result = await fetch(`http://${SERVER_DOMAIN}/uploadfile`, {
        method: "POST",
        body: formData
      });
    } else { 
      result = await fetch(`http://${SERVER_DOMAIN}/prompt`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        // forward the messages in the chat to the API
        body: JSON.stringify({
          // chat_id:"2",
          prompt: messages[messages.length-1].content[0].text
        }),
        // if the user hits the "cancel" button or escape keyboard key, cancel the request
        signal: abortSignal,
      });
    }
    const data = await result.json();
    return {
      content: [
        {
          type: "text",
          text: data.message.content,
        },
      ],
    };
  },
};
 
export function ReltaRuntimeProvider({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  const runtime = useLocalRuntime(MyModelAdapter, {
    adapters: {
        attachments: new SimpleTextAttachmentAdapter()
        ,
        feedback: {
            submit: ({ type, message }) => {
                fetch(`http://${SERVER_DOMAIN}/feedback`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(
                       {type:type, message: message}
                    ),
                })
                .then(response => response.json())
                .then(data => console.log('Feedback submitted:', data))
                .catch(error => console.error('Error submitting feedback:', error));
              console.log({ type, message });
            },
          }
    }
  } )
 
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}