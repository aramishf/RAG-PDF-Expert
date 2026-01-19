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

export interface Document {
    filename: string;
    size_mb: number;
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

    if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Upload failed (${res.status}): ${errorText.substring(0, 100)}`);
    }
    const data = await res.json();
    if (data.status === 'error') throw new Error(data.message || 'Upload failed');
    return data;
}

export async function sendChat(question: string): Promise<{ answer: string; citations: Citation[] }> {
    const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
    });

    if (!res.ok) {
        const text = await res.text();
        try {
            const error = JSON.parse(text);
            throw new Error(error.detail || 'Chat failed');
        } catch (e) {
            // If valid JSON parsing failed, use the raw text
            // Check if it looks like a JSON syntax error
            if (e instanceof SyntaxError || (e instanceof Error && e.message.includes('Unexpected token'))) {
                // Proceed to throw the text error below
            } else {
                // It might be our own throw above
                throw e;
            }
            throw new Error(`Chat failed (${res.status}): ${text.substring(0, 200)}`);
        }
    }
    return res.json();
}

export async function listDocuments(): Promise<{ documents: Document[]; total: number }> {
    const res = await fetch(`${API_URL}/list-documents`);
    if (!res.ok) {
        throw new Error('Failed to fetch documents list');
    }
    return res.json();
}
