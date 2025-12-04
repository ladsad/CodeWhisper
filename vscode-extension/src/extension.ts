import * as vscode from 'vscode';
import axios from 'axios';

export function activate(context: vscode.ExtensionContext) {
    console.log('CodeWhisper extension is now active!');

    let disposable = vscode.commands.registerCommand('codewhisper.generateDocs', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor found.');
            return;
        }

        const selection = editor.selection;
        const text = editor.document.getText(selection);

        if (!text) {
            vscode.window.showErrorMessage('Please select some code to document.');
            return;
        }

        try {
            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Generating documentation...",
                cancellable: false
            }, async (progress) => {
                const response = await axios.post('http://localhost:8000/api/v1/generate', {
                    code: text,
                    language: editor.document.languageId
                });

                const docstring = response.data.docstring;

                if (docstring) {
                    editor.edit(editBuilder => {
                        editBuilder.insert(selection.start, docstring + '\n');
                    });
                    vscode.window.showInformationMessage('Documentation generated successfully!');
                } else {
                    vscode.window.showWarningMessage('No documentation returned from backend.');
                }
            });
        } catch (error) {
            vscode.window.showErrorMessage(`Error generating docs: ${error}`);
            console.error(error);
        }
    });

    context.subscriptions.push(disposable);
}

export function deactivate() { }
