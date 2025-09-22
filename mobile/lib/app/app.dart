import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../core/constants/app_constants.dart';
import '../core/network/api_client.dart';
import '../data/datasources/remote/gym_api_service.dart';
import '../data/repositories/gym_repository_impl.dart';
import '../presentation/providers/gym_provider.dart';
import '../presentation/providers/chat_provider.dart';
import 'routes.dart';
import 'themes.dart';

class GymPulseApp extends StatelessWidget {
  const GymPulseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // API and repository providers
        Provider<GymApiService>(
          create: (_) => GymApiService(ApiClient.createDio()),
        ),
        ProxyProvider<GymApiService, GymRepositoryImpl>(
          update: (_, apiService, __) => GymRepositoryImpl(apiService: apiService),
        ),

        // State management providers
        ChangeNotifierProxyProvider<GymRepositoryImpl, GymProvider>(
          create: (context) => GymProvider(
            gymRepository: context.read<GymRepositoryImpl>(),
          ),
          update: (_, repository, previous) =>
              previous ?? GymProvider(gymRepository: repository),
        ),
        ChangeNotifierProvider<ChatProvider>(
          create: (_) => ChatProvider(),
        ),
      ],
      child: Consumer<GymProvider>(
        builder: (context, gymProvider, child) {
          return MaterialApp.router(
            title: AppConstants.appName,
            debugShowCheckedModeBanner: false,
            theme: AppThemes.lightTheme,
            darkTheme: AppThemes.darkTheme,
            themeMode: ThemeMode.system,
            routerConfig: appRouter,
          );
        },
      ),
    );
  }
}

class AppInitializer extends StatefulWidget {
  final Widget child;

  const AppInitializer({
    super.key,
    required this.child,
  });

  @override
  State<AppInitializer> createState() => _AppInitializerState();
}

class _AppInitializerState extends State<AppInitializer> {
  bool _isInitialized = false;

  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    try {
      // Load environment variables
      await dotenv.load(fileName: ".env");

      // Initialize Hive for local storage
      await Hive.initFlutter();

      // Initialize other services
      // TODO: Add other initialization logic here

      setState(() {
        _isInitialized = true;
      });
    } catch (e) {
      // Handle initialization error
      debugPrint('App initialization error: $e');
      setState(() {
        _isInitialized = true; // Continue anyway
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_isInitialized) {
      return const MaterialApp(
        home: Scaffold(
          body: Center(
            child: CircularProgressIndicator(),
          ),
        ),
      );
    }

    return widget.child;
  }
}
