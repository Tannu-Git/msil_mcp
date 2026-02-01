# Application Load Balancer Module for MSIL MCP

resource "aws_lb" "main" {
  name               = "${var.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.subnet_ids

  enable_deletion_protection = var.deletion_protection

  access_logs {
    bucket  = var.access_logs_bucket
    prefix  = "alb-logs"
    enabled = var.access_logs_bucket != "" ? true : false
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-alb"
    }
  )
}

# HTTPS Listener
resource "aws_lb_listener" "https" {
  count = var.certificate_arn != "" ? 1 : 0

  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "application/json"
      message_body = "{\"error\": \"Not Found\"}"
      status_code  = "404"
    }
  }

  tags = var.tags
}

# HTTP Listener (redirect to HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = var.certificate_arn != "" ? "redirect" : "fixed-response"

    dynamic "redirect" {
      for_each = var.certificate_arn != "" ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    dynamic "fixed_response" {
      for_each = var.certificate_arn == "" ? [1] : []
      content {
        content_type = "application/json"
        message_body = "{\"error\": \"Not Found\"}"
        status_code  = "404"
      }
    }
  }

  tags = var.tags
}

# Target Groups
resource "aws_lb_target_group" "mcp_server" {
  name        = "${var.name_prefix}-mcp-server"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-mcp-server-tg"
    }
  )
}

resource "aws_lb_target_group" "chat_ui" {
  name        = "${var.name_prefix}-chat-ui"
  port        = 3001
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-chat-ui-tg"
    }
  )
}

resource "aws_lb_target_group" "admin_ui" {
  name        = "${var.name_prefix}-admin-ui"
  port        = 3002
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-admin-ui-tg"
    }
  )
}

resource "aws_lb_target_group" "mock_api" {
  name        = "${var.name_prefix}-mock-api"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-mock-api-tg"
    }
  )
}

# Listener Rules (if HTTPS is enabled)
resource "aws_lb_listener_rule" "mcp_server" {
  count = var.certificate_arn != "" ? 1 : 0

  listener_arn = aws_lb_listener.https[0].arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.mcp_server.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/mcp/*", "/health", "/docs", "/openapi.json"]
    }
  }

  tags = var.tags
}

resource "aws_lb_listener_rule" "chat_ui" {
  count = var.certificate_arn != "" ? 1 : 0

  listener_arn = aws_lb_listener.https[0].arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.chat_ui.arn
  }

  condition {
    host_header {
      values = ["chat.*", "*.chat.*"]
    }
  }

  tags = var.tags
}

resource "aws_lb_listener_rule" "admin_ui" {
  count = var.certificate_arn != "" ? 1 : 0

  listener_arn = aws_lb_listener.https[0].arn
  priority     = 300

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.admin_ui.arn
  }

  condition {
    host_header {
      values = ["admin.*", "*.admin.*"]
    }
  }

  tags = var.tags
}
