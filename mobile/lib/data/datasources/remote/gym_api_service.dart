import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../../models/api/branch_response.dart';
import '../../models/api/machine_response.dart';
import '../../models/api/alert_response.dart';
import '../../models/api/chat_response.dart';

part 'gym_api_service.g.dart';

/// Retrofit API service for GymPulse backend
@RestApi()
abstract class GymApiService {
  factory GymApiService(Dio dio, {String baseUrl}) = _GymApiService;

  // Branch endpoints
  @GET('/branches')
  Future<BranchesResponse> getBranches();

  @GET('/branches/{branchId}/peak-hours')
  Future<PeakHoursResponse> getBranchPeakHours(@Path() String branchId);

  // Machine endpoints
  @GET('/branches/{branchId}/categories/{category}/machines')
  Future<MachinesResponse> getMachines(
    @Path() String branchId,
    @Path() String category,
  );

  @GET('/machines/{machineId}/history')
  Future<MachineHistoryResponse> getMachineHistory(
    @Path() String machineId,
    @Query('range') String range,
  );

  @GET('/forecast/machine/{machineId}')
  Future<MachineForecastResponse> getMachineForecast(
    @Path() String machineId,
    @Query('minutes') int minutes,
  );

  // Alert endpoints
  @POST('/alerts')
  Future<AlertResponse> createAlert(@Body() CreateAlertRequest request);

  @GET('/alerts')
  Future<AlertsListResponse> listAlerts(@Query('userId') String userId);

  @PUT('/alerts/{alertId}')
  Future<AlertResponse> updateAlert(
    @Path() String alertId,
    @Body() UpdateAlertRequest request,
  );

  @DELETE('/alerts/{alertId}')
  Future<void> cancelAlert(@Path() String alertId);

  // Chat endpoints
  @POST('/chat')
  Future<ChatResponse> sendChatMessage(@Body() ChatRequest request);

  // Tool endpoints for chatbot
  @POST('/tools/availability')
  Future<AvailabilityToolResponse> getAvailabilityByCategory(
    @Body() AvailabilityToolRequest request,
  );

  @POST('/tools/route-matrix')
  Future<RouteMatrixResponse> getRouteMatrix(
    @Body() RouteMatrixRequest request,
  );

  // Health check
  @GET('/health')
  Future<HealthResponse> healthCheck();
}