import 'package:go_router/go_router.dart';
import 'package:flutter/material.dart';

import '../presentation/pages/branch/branch_list_page.dart';
import '../presentation/pages/machine/machine_list_page.dart';
import '../presentation/pages/chat/chat_page.dart';
import '../domain/entities/branch.dart';
import '../shared/enums/equipment_category.dart';

class AppRoutes {
  static const String home = '/';
  static const String branches = '/branches';
  static const String machines = '/machines';
  static const String machineDetail = '/machine-detail';
  static const String settings = '/settings';
  static const String chat = '/chat';
}

final GoRouter appRouter = GoRouter(
  initialLocation: AppRoutes.home,
  routes: [
    GoRoute(
      path: AppRoutes.home,
      name: 'home',
      builder: (context, state) => const BranchListPage(),
    ),
    GoRoute(
      path: AppRoutes.branches,
      name: 'branches',
      builder: (context, state) => const BranchListPage(),
    ),
    GoRoute(
      path: AppRoutes.machines,
      name: 'machines',
      builder: (context, state) {
        final extra = state.extra as Map<String, dynamic>?;
        if (extra == null) {
          // If no extra data, redirect to branches
          return const BranchListPage();
        }

        final branch = extra['branch'] as Branch;
        final category = extra['category'] as EquipmentCategory;

        return MachineListPage(
          branch: branch,
          category: category,
        );
      },
    ),
    // Chat route
    GoRoute(
      path: AppRoutes.chat,
      name: 'chat',
      builder: (context, state) => const ChatPage(),
    ),
    // Add more routes as needed
    // GoRoute(
    //   path: AppRoutes.settings,
    //   name: 'settings',
    //   builder: (context, state) => const SettingsPage(),
    // ),
  ],
  errorBuilder: (context, state) => Scaffold(
    appBar: AppBar(
      title: const Text('Page Not Found'),
    ),
    body: Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.error_outline,
            size: 64,
            color: Colors.grey,
          ),
          const SizedBox(height: 16),
          Text(
            'Page Not Found',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          Text(
            'The page you requested could not be found.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () => context.go(AppRoutes.home),
            child: const Text('Go to Home'),
          ),
        ],
      ),
    ),
  ),
);
