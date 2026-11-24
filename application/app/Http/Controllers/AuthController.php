<?php

namespace App\Http\Controllers;

use App\Auth\WorkspaceAccess;
use App\Http\Requests\LoginRequest;
use App\Services\AuthAudit;
use App\Services\LoginService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Auth;

class AuthController extends Controller
{
    public function login(LoginRequest $request, LoginService $service): JsonResponse
    {
        $credentials = $request->validated();
        $user = $service->login($request, $credentials['username'], $credentials['password']);

        return response()->json(WorkspaceAccess::session($user));
    }

    public function session(Request $request): JsonResponse
    {
        return response()->json(WorkspaceAccess::session($request->user()));
    }

    public function logout(Request $request, AuthAudit $audit): Response
    {
        $audit->record('logout', $request->user(), $request);
        Auth::guard('web')->logout();
        $request->session()->invalidate();
        $request->session()->regenerateToken();

        return response()->noContent();
    }
}
