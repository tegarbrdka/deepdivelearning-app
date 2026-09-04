@echo off
echo ========================================
echo Fixing Frontend Issues
echo ========================================
echo.

cd frontend

echo [1/3] Clearing Vite cache...
if exist "node_modules\.vite" (
    rmdir /s /q "node_modules\.vite"
    echo ✓ Vite cache cleared
) else (
    echo ✓ No Vite cache found
)

echo.
echo [2/3] Clearing browser cache...
echo Please clear your browser cache manually:
echo - Chrome/Edge: Ctrl+Shift+Delete
echo - Or use Incognito/Private mode
echo.

echo [3/3] Restarting frontend server...
echo Close any running frontend server first (Ctrl+C in terminal)
echo.
pause

npm run dev
