from django import forms
from django.core.exceptions import ValidationError
from .models import AssignmentTask
import os

class AssignmentUploadForm(forms.ModelForm):
    class Meta:
        model = AssignmentTask
        fields = ['assignment_file']
        widgets = {
            'assignment_file': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'file-upload',
                'accept': '.pdf,.docx,.png,.jpg'
            })
        }

    def clean_assignment_file(self):
        file = self.cleaned_data.get('assignment_file')
        if file:
            # Check file size (5MB limit)
            max_size = 5 * 1024 * 1024
            if file.size > max_size:
                raise ValidationError("File size cannot exceed 5MB.")
            
            # Check file extension
            valid_extensions = ['.pdf', '.docx', '.png', '.jpg']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError("Unsupported file format. Allowed formats: PDF, DOCX, PNG, JPG.")
        return file
