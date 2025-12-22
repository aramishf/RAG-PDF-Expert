const API_URL = 'http://localhost:8000';

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    citations?: Citation[];
}

export interface Citation {
    source: string;
    page: number;
    score: number;
    text: string;
}

export async function uploadFiles(files: File[]) {
    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file);
    });

    const res = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
    });

    if (!res.ok) throw new Error('Upload failed');
    return res.json();
}

export async function sendChat(question: string): Promise<{ answer: string; citations: Citation[] }> {
    const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Chat failed');
    }
    return res.json();
}
