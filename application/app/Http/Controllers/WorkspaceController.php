<?php

namespace App\Http\Controllers;

use App\Auth\WorkspaceAccess;
use App\Services\AuthAudit;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class WorkspaceController extends Controller
{
    public function __invoke(Request $request, string $workspace, AuthAudit $audit): JsonResponse
    {
        $user = $request->user();

        if (! WorkspaceAccess::allows($user, $workspace)) {
            $audit->record('workspace.denied', $user, $request);
            abort(403);
        }

        return response()->json([
            ...WorkspaceAccess::session($user),
            'workspace' => '/workspace/'.$workspace,
            'permissions' => $user->getAllPermissions()->pluck('name')->sort()->values()->all(),
        ]);
    }
}
