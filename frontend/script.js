// Simple authentication system (no Supabase required)
const AUTH_KEY = 'lawyeredai_auth'

class NYCLegalAssistant {
    constructor() {
        this.userId = this.generateUserId();
        this.sessionId = null;
        this.isProcessing = false;
        this.checkAuthAndInitialize();
    }

    async checkAuthAndInitialize() {
        // Check if user is authenticated
        const session = JSON.parse(localStorage.getItem(AUTH_KEY) || 'null');
        
        if (!session || !session.user) {
            // Not authenticated, redirect to login
            window.location.href = '/login';
            return;
        }
        
        // User is authenticated, initialize the app
        this.userId = session.user.id;
        this.initializeElements();
        this.attachEventListeners();
    }

    generateUserId() {
        return 'user_' + Math.random().toString(36).substr(2, 9);
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        // Modal elements
        this.modal = document.getElementById('demandNoticeModal');
        this.demandForm = document.getElementById('demandNoticeForm');
        this.generatedNotice = document.getElementById('generatedNotice');
        this.noticeContent = document.getElementById('noticeContent');
    }

    attachEventListeners() {
        // Chat functionality
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key handling (improved)
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Input changes
        this.messageInput.addEventListener('input', () => {
            this.adjustTextareaHeight();
        });

        // Modal functionality
        document.getElementById('closeModal').addEventListener('click', () => this.closeModal());
        document.getElementById('cancelDemand').addEventListener('click', () => this.closeModal());
        this.demandForm.addEventListener('submit', (e) => this.handleDemandFormSubmit(e));
        
        // Updated download handlers for PDF and text
        document.getElementById('downloadPDF').addEventListener('click', () => this.downloadPDF());
        document.getElementById('downloadText').addEventListener('click', () => this.downloadText());
        document.getElementById('editNotice').addEventListener('click', () => this.editNotice());

        // Close modal on outside click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        // Logout functionality
        document.getElementById('logoutBtn').addEventListener('click', () => this.handleLogout());
    }

    async handleLogout() {
        try {
            localStorage.removeItem(AUTH_KEY);
            window.location.href = '/login';
        } catch (error) {
            console.error('Logout error:', error);
        }
    }

    adjustTextareaHeight() {
        const textarea = this.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isProcessing) return;

        // Add user message to chat immediately
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.adjustTextareaHeight();
        this.showTypingIndicator(true);
        this.setProcessing(true);

        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: this.userId,
                    session_id: this.sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Update session ID
            this.sessionId = data.session_id;
            
            // Hide typing indicator before showing response
            this.showTypingIndicator(false);
            
            // Add AI response to chat
            this.addMessage(data.response, 'assistant', data.can_generate_demand_notice);

        } catch (error) {
            console.error('Error sending message:', error);
            this.showTypingIndicator(false);
            this.addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        } finally {
            this.setProcessing(false);
        }
    }

    addMessage(content, role, canGenerateDemand = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Convert basic markdown-style formatting
        const formattedContent = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
        
        contentDiv.innerHTML = `<p>${formattedContent}</p>`;
        
        // Add demand notice button if applicable
        if (canGenerateDemand && role === 'assistant') {
            const demandButton = document.createElement('button');
            demandButton.className = 'button primary';
            demandButton.textContent = '📝 Generate Demand Notice';
            demandButton.style.marginTop = '0.75rem';
            demandButton.addEventListener('click', () => this.openDemandModal());
            contentDiv.appendChild(demandButton);
        }
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        
        // Smooth scroll to bottom
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    showTypingIndicator(show) {
        if (show && !this.isProcessing) return;
        
        if (show) {
            this.typingIndicator.classList.remove('hidden');
            // Scroll to show typing indicator
            setTimeout(() => {
                this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
            }, 100);
        } else {
            this.typingIndicator.classList.add('hidden');
        }
    }

    setProcessing(processing) {
        this.isProcessing = processing;
        this.sendButton.disabled = processing;
        this.messageInput.disabled = processing;
        
        if (processing) {
            this.sendButton.style.opacity = '0.7';
        } else {
            this.sendButton.style.opacity = '1';
        }
    }

    openDemandModal() {
        console.log('Opening demand notice modal...');
        
        // Show modal
        this.modal.classList.remove('hidden');
        
        // Show form, hide generated notice
        document.getElementById('demandFormSection').classList.remove('hidden');
        document.getElementById('generatedNoticeSection').classList.add('hidden');
        
        // Focus on first input
        setTimeout(() => {
            const firstInput = document.getElementById('complainantName');
            if (firstInput) {
                firstInput.focus();
            }
        }, 100);
    }

    closeModal() {
        console.log('Closing modal...');
        this.modal.classList.add('hidden');
        
        // Reset form
        this.demandForm.reset();
        
        // Show form, hide generated notice
        document.getElementById('demandFormSection').classList.remove('hidden');
        document.getElementById('generatedNoticeSection').classList.add('hidden');
    }

    async handleDemandFormSubmit(e) {
        e.preventDefault();
        console.log('Form submitted...');
        
        const submitButton = document.getElementById('generateDemand');
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Generating...';
        submitButton.disabled = true;
    
        const demandData = this.getFormData();
    
        try {
            const response = await fetch('/api/demand-notice/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(demandData)
            });
    
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
    
            const data = await response.json();
            
            // Show generated notice
            document.getElementById('noticeContent').value = data.notice_content;
            
            // Switch views
            document.getElementById('demandFormSection').classList.add('hidden');
            document.getElementById('generatedNoticeSection').classList.remove('hidden');
    
            console.log('Notice generated successfully');
    
        } catch (error) {
            console.error('Error generating demand notice:', error);
            alert('Error generating demand notice. Please try again.');
        } finally {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }
    }
    
    editNotice() {
        console.log('Editing notice...');
        // Switch back to form view
        document.getElementById('generatedNoticeSection').classList.add('hidden');
        document.getElementById('demandFormSection').classList.remove('hidden');
    }

    getFormData() {
        return {
            user_id: this.userId,
            session_id: this.sessionId,
            complainant_name: document.getElementById('complainantName').value,
            complainant_address: document.getElementById('complainantAddress').value,
            complainant_contact: document.getElementById('complainantContact').value,
            respondent_name: document.getElementById('respondentName').value,
            respondent_address: document.getElementById('respondentAddress').value,
            issue_description: document.getElementById('issueDescription').value,
            amount_claimed: document.getElementById('amountClaimed').value,
            resolution_sought: document.getElementById('resolutionSought').value,
            // New NYC template fields
            incident_date: document.getElementById('incidentDate')?.value || null,
            item_service: document.getElementById('itemService')?.value || null,
            contact_method: document.getElementById('contactMethod')?.value || 'email / phone'
        };
    }

    async downloadPDF() {
        const downloadBtn = document.getElementById('downloadPDF');
        const originalText = downloadBtn.textContent;
        downloadBtn.textContent = 'Generating PDF...';
        downloadBtn.disabled = true;

        try {
            const demandData = this.getFormData();
            
            const response = await fetch('/api/demand-notice/generate-pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(demandData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Download the PDF file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `nyc_demand_notice_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

        } catch (error) {
            console.error('Error downloading PDF:', error);
            alert('Error downloading PDF. Please try again.');
        } finally {
            downloadBtn.textContent = originalText;
            downloadBtn.disabled = false;
        }
    }

    async downloadText() {
        const downloadBtn = document.getElementById('downloadText');
        const originalText = downloadBtn.textContent;
        downloadBtn.textContent = 'Generating...';
        downloadBtn.disabled = true;

        try {
            const demandData = this.getFormData();
            
            const response = await fetch('/api/demand-notice/download-text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(demandData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Download the text file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `nyc_demand_notice_${new Date().toISOString().split('T')[0]}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

        } catch (error) {
            console.error('Error downloading text file:', error);
            alert('Error downloading text file. Please try again.');
        } finally {
            downloadBtn.textContent = originalText;
            downloadBtn.disabled = false;
        }
    }

    // Keep the old downloadNotice method for backward compatibility
    downloadNotice() {
        this.downloadText();
    }

    editNotice() {
        this.generatedNotice.classList.add('hidden');
        this.demandForm.classList.remove('hidden');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Prevent multiple initializations
    if (!window.legalAssistant) {
        window.legalAssistant = new NYCLegalAssistant();
    }
});