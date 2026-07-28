import os
import subprocess
import tempfile
from datetime import datetime
from django.conf import settings
from django.http import FileResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser

def get_db_credentials():
    db_settings = settings.DATABASES['default']
    return {
        'DB_NAME': db_settings['NAME'],
        'DB_USER': db_settings['USER'],
        'DB_PASSWORD': db_settings['PASSWORD'],
        'DB_HOST': db_settings.get('HOST', 'localhost'),
        'DB_PORT': db_settings.get('PORT', '5432')
    }

@api_view(['GET'])
@permission_classes([IsAdminUser])
def backup_database(request):
    creds = get_db_credentials()
    
    # Environment variables for subprocess
    env = os.environ.copy()
    env['PGPASSWORD'] = creds['DB_PASSWORD']
    
    # Generate backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"backup_{creds['DB_NAME']}_{timestamp}.sql"
    
    # We will use a NamedTemporaryFile to store the dump, which is then sent
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sql')
    temp_file.close()
    
    try:
        # Construct pg_dump command
        # Plain SQL format, include pre-data, data, and post-data
        command = [
            'pg_dump',
            '-U', creds['DB_USER'],
            '-h', creds['DB_HOST'],
            '-p', str(creds['DB_PORT']),
            '-F', 'p', # Plain text
            '--section=pre-data',
            '--section=data',
            '--section=post-data',
            '--clean', # Include DROP statements so it can be restored over an existing DB
            '-f', temp_file.name,
            creds['DB_NAME']
        ]
        
        process = subprocess.run(command, env=env, capture_output=True, text=True)
        
        if process.returncode != 0:
            return JsonResponse({'error': 'Backup failed', 'details': process.stderr}, status=500)
            
        # Return the file as a download
        file_response = FileResponse(open(temp_file.name, 'rb'), as_attachment=True, filename=filename)
        return file_response
        
    except Exception as e:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def restore_database(request):
    if 'backup_file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
        
    backup_file = request.FILES['backup_file']
    creds = get_db_credentials()
    
    env = os.environ.copy()
    env['PGPASSWORD'] = creds['DB_PASSWORD']
    
    # Save uploaded file to temp
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sql')
    for chunk in backup_file.chunks():
        temp_file.write(chunk)
    temp_file.close()
    
    try:
        command = [
            'psql',
            '-U', creds['DB_USER'],
            '-h', creds['DB_HOST'],
            '-p', str(creds['DB_PORT']),
            '-d', creds['DB_NAME'],
            '-f', temp_file.name
        ]
        
        process = subprocess.run(command, env=env, capture_output=True, text=True)
        
        if process.returncode != 0:
            return JsonResponse({'error': 'Restore failed', 'details': process.stderr}, status=500)
            
        return JsonResponse({'message': 'Database restored successfully!'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
